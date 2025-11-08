import base64
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib as mpl
import mplfinance as mpf
import pandas as pd
from matplotlib import font_manager, pyplot as plt
from matplotlib.lines import Line2D

MA_WINDOWS = (5, 10, 20, 30, 60, 120, 240)
MA_COLORS = (
    "#d62728",  # MA5 红
    "#1f77b4",  # MA10 蓝
    "#2ca02c",  # MA20 绿
    "#ff7f0e",  # MA30 橙
    "#9467bd",  # MA60 紫
    "#8c564b",  # MA120 棕
    "#e377c2",  # MA240 粉
)
BB_WINDOW = 20
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9


class KlineHelper:
    """生成 K 线图并提供 Base64 编码工具。"""

    def __init__(self) -> None:
        self._mpf_style, self._chosen_font = self._init_plot_style()

    def create_kline(self, raw_data: Sequence[Mapping[str, Any]]) -> Path:
        """根据行情数据生成 K 线图并保存到临时文件。"""

        df = self._prepare_dataframe(raw_data)
        add_plots = self._build_add_plots(df)
        last_date = df.index.max().strftime("%Y-%m-%d")
        title = f"{df.iloc[0]['name']}({df.iloc[0]['code']}) 日K {last_date}"

        fig, axes = mpf.plot(
            df,
            type="candle",
            mav=MA_WINDOWS,
            mavcolors=MA_COLORS,
            volume=True,
            addplot=add_plots,
            figratio=(16, 9),
            figsize=(16, 9),
            tight_layout=True,
            style=self._mpf_style,
            title=title,
            ylabel="价格",
            ylabel_lower="成交量",
            panel_ratios=(6, 2, 2),
            datetime_format="%Y-%m-%d",
            xrotation=45,
            block=False,
            returnfig=True,
        )

        self._decorate_axes(axes, df, last_date)

        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        output_path = Path(temp_path)
        fig.savefig(output_path, format="png", bbox_inches="tight")
        plt.close(fig)
        return output_path

    @staticmethod
    def to_base64(image_path: str | Path) -> str:
        """读取图片文件并返回 Base64 编码。"""

        data = Path(image_path).read_bytes()
        return base64.b64encode(data).decode("ascii")

    @staticmethod
    def _prepare_dataframe(raw_data: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
        if not raw_data:
            raise ValueError("raw_data 不能为空")

        df = pd.DataFrame(raw_data).copy()
        required = ("code", "name", "time", "open", "high", "low", "close", "volume")
        for field in required:
            if field not in df.columns:
                raise KeyError(f"缺少必要字段: {field}")

        df["Date"] = pd.to_datetime(df["time"].astype(str), format="%Y%m%d")
        df = df.set_index("Date").sort_index()

        df = df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        })
        return df

    @staticmethod
    def _build_add_plots(df: pd.DataFrame) -> list[Any]:
        add_plots: list[Any] = []

        if len(df) >= BB_WINDOW:
            mid = df["Close"].rolling(BB_WINDOW).mean()
            std = df["Close"].rolling(BB_WINDOW).std(ddof=0)
            upper = mid + 2 * std
            lower = mid - 2 * std
            add_plots.extend(
                [
                    mpf.make_addplot(upper, color="#8c8c8c", width=0.8, linestyle="--", label="Bollinger Upper"),
                    mpf.make_addplot(mid, color="#b3b3b3", width=0.8, label="Bollinger Middle"),
                    mpf.make_addplot(lower, color="#8c8c8c", width=0.8, linestyle="--", label="Bollinger Lower"),
                ]
            )

        ema_fast = df["Close"].ewm(span=MACD_FAST, adjust=False).mean()
        ema_slow = df["Close"].ewm(span=MACD_SLOW, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=MACD_SIGNAL, adjust=False).mean()
        macd_hist = macd - macd_signal
        hist_colors = ["#d62728" if value >= 0 else "#2ca02c" for value in macd_hist]

        add_plots.extend(
            [
                mpf.make_addplot(macd, panel=2, color="#d62728", width=1.0, label="MACD", ylabel="MACD"),
                mpf.make_addplot(macd_signal, panel=2, color="#1f77b4", width=1.0, linestyle="--", label="Signal"),
                mpf.make_addplot(macd_hist, panel=2, type="bar", color=hist_colors, alpha=0.5, label="Histogram"),
            ]
        )
        return add_plots

    def _decorate_axes(self, axes: Sequence[Any], df: pd.DataFrame, last_date: str) -> None:
        if not axes:
            return

        ma_handles = [Line2D([0], [0], color=color, linewidth=1.8) for color in MA_COLORS]
        ma_labels = [f"MA{window}" for window in MA_WINDOWS]

        bb_handles: list[Line2D] = []
        bb_labels: list[str] = []
        if len(df) >= BB_WINDOW:
            bb_handles = [
                Line2D([0], [0], color="#8c8c8c", linewidth=1.0, linestyle="--"),
                Line2D([0], [0], color="#b3b3b3", linewidth=1.0),
                Line2D([0], [0], color="#8c8c8c", linewidth=1.0, linestyle="--"),
            ]
            bb_labels = ["Bollinger Upper", "Bollinger Middle", "Bollinger Lower"]

        axes[0].legend(ma_handles + bb_handles, ma_labels + bb_labels, loc="upper left", ncol=2, fontsize=9)
        axes[-1].text(
            1.0,
            -0.28,
            f"最新日期: {last_date}",
            transform=axes[-1].transAxes,
            ha="right",
            va="top",
            fontsize=9,
            color="#333333",
        )

    @staticmethod
    def _enable_chinese_font() -> str | None:
        candidate_files = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB W3.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/arphic/ukai.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ]
        preferred_fonts = [
            "PingFang SC",
            "Microsoft YaHei",
            "SimHei",
            "Noto Sans CJK SC",
            "WenQuanYi Micro Hei",
            "Heiti SC",
            "STHeiti",
            "Arial Unicode MS",
        ]

        available_fonts = {f.name for f in font_manager.fontManager.ttflist}
        chosen_font = next((f for f in preferred_fonts if f in available_fonts), None)

        registered = False
        if not chosen_font:
            for font_path in candidate_files:
                if os.path.exists(font_path):
                    try:
                        font_manager.fontManager.addfont(font_path)
                        registered = True
                    except Exception as exc:  # noqa: BLE001
                        print(f"警告: 加载字体 {font_path} 失败: {exc}")

            if registered:
                reload_fn = getattr(font_manager, "_load_fontmanager", None)
                if callable(reload_fn):
                    reload_fn(try_read_cache=True)
                available_fonts = {f.name for f in font_manager.fontManager.ttflist}
                chosen_font = next((f for f in preferred_fonts if f in available_fonts), None)

        if chosen_font:
            mpl.rcParams["font.family"] = [chosen_font]
            existing = mpl.rcParams.get("font.sans-serif", [])
            if isinstance(existing, str):
                existing = [existing]
            mpl.rcParams["font.sans-serif"] = [chosen_font] + [f for f in existing if f != chosen_font]
        else:
            msg = "提示: 未找到常见中文字体，中文文字可能无法正常显示；请安装 Noto Sans CJK SC 等字体。"
            if registered:
                msg = "提示: 字体已尝试注册，但 Matplotlib 无法识别；请检查字体安装是否正确。"
            print(msg)

        mpl.rcParams["axes.unicode_minus"] = False
        return chosen_font

    def _init_plot_style(self) -> tuple[Any, str | None]:
        chosen_font = self._enable_chinese_font()
        style_kwargs: dict[str, Any] = {}
        if chosen_font:
            style_kwargs["rc"] = {
                "font.family": chosen_font,
                "font.sans-serif": [chosen_font],
                "axes.unicode_minus": False,
            }

        market_colors = mpf.make_marketcolors(up="red", down="green", inherit=True)
        mpf_style = mpf.make_mpf_style(base_mpf_style="yahoo", marketcolors=market_colors, **style_kwargs)
        return mpf_style, chosen_font

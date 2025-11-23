#!/usr/bin/env python3
"""测试 Supabase 数据库连接延迟"""

import time
import statistics
import psycopg2
from psycopg2 import pool

# 数据库连接字符串
DB_URL = "postgresql://postgres:IURSG6o3wEsQKHiN@db.jmuqxmdtwjpibskpyaxk.supabase.co:5432/postgres?options=-csearch_path%3Dgoogle_adk"
DB_URL = "postgresql://postgres:CjqH7NBNN4RZLPdP@db.ydegsslcbzlyifilkxeg.supabase.co:5432/postgres?options=-csearch_path%3Dgoogle_adk"
def test_connection_latency(iterations=10):
    """测试建立连接的延迟"""
    print(f"\n{'='*60}")
    print("测试 1: 建立连接延迟")
    print(f"{'='*60}")

    latencies = []
    for i in range(iterations):
        start = time.perf_counter()
        try:
            conn = psycopg2.connect(DB_URL)
            conn.close()
            elapsed = (time.perf_counter() - start) * 1000  # 转换为毫秒
            latencies.append(elapsed)
            print(f"第 {i+1:2d} 次: {elapsed:7.2f} ms")
        except Exception as e:
            print(f"第 {i+1:2d} 次: 失败 - {e}")

    if latencies:
        print(f"\n统计结果:")
        print(f"  平均延迟: {statistics.mean(latencies):7.2f} ms")
        print(f"  最小延迟: {min(latencies):7.2f} ms")
        print(f"  最大延迟: {max(latencies):7.2f} ms")
        print(f"  标准差:   {statistics.stdev(latencies):7.2f} ms" if len(latencies) > 1 else "  标准差:   N/A")

    return latencies

def test_query_latency(iterations=10):
    """测试简单查询延迟（复用连接）"""
    print(f"\n{'='*60}")
    print("测试 2: 简单查询延迟（SELECT 1）")
    print(f"{'='*60}")

    latencies = []
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()

        for i in range(iterations):
            start = time.perf_counter()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
            print(f"第 {i+1:2d} 次: {elapsed:7.2f} ms")

        cursor.close()
        conn.close()

        if latencies:
            print(f"\n统计结果:")
            print(f"  平均延迟: {statistics.mean(latencies):7.2f} ms")
            print(f"  最小延迟: {min(latencies):7.2f} ms")
            print(f"  最大延迟: {max(latencies):7.2f} ms")
            print(f"  标准差:   {statistics.stdev(latencies):7.2f} ms" if len(latencies) > 1 else "  标准差:   N/A")

    except Exception as e:
        print(f"查询测试失败: {e}")

    return latencies

def test_ping_latency(iterations=10):
    """测试 PING 延迟（SELECT NOW()）"""
    print(f"\n{'='*60}")
    print("测试 3: PING 延迟（SELECT NOW()）")
    print(f"{'='*60}")

    latencies = []
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()

        for i in range(iterations):
            start = time.perf_counter()
            cursor.execute("SELECT NOW()")
            cursor.fetchone()
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
            print(f"第 {i+1:2d} 次: {elapsed:7.2f} ms")

        cursor.close()
        conn.close()

        if latencies:
            print(f"\n统计结果:")
            print(f"  平均延迟: {statistics.mean(latencies):7.2f} ms")
            print(f"  最小延迟: {min(latencies):7.2f} ms")
            print(f"  最大延迟: {max(latencies):7.2f} ms")
            print(f"  标准差:   {statistics.stdev(latencies):7.2f} ms" if len(latencies) > 1 else "  标准差:   N/A")

    except Exception as e:
        print(f"PING 测试失败: {e}")

    return latencies

def test_table_query_latency(iterations=5):
    """测试实际表查询延迟"""
    print(f"\n{'='*60}")
    print("测试 4: 实际表查询延迟")
    print(f"{'='*60}")

    latencies = []
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()

        # 先获取一个表名
        cursor.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'google_adk'
            LIMIT 1
        """)
        result = cursor.fetchone()

        if result:
            table_name = result[0]
            print(f"测试表: google_adk.{table_name}")

            for i in range(iterations):
                start = time.perf_counter()
                cursor.execute(f"SELECT * FROM google_adk.{table_name} LIMIT 1")
                cursor.fetchall()
                elapsed = (time.perf_counter() - start) * 1000
                latencies.append(elapsed)
                print(f"第 {i+1:2d} 次: {elapsed:7.2f} ms")

            if latencies:
                print(f"\n统计结果:")
                print(f"  平均延迟: {statistics.mean(latencies):7.2f} ms")
                print(f"  最小延迟: {min(latencies):7.2f} ms")
                print(f"  最大延迟: {max(latencies):7.2f} ms")
                print(f"  标准差:   {statistics.stdev(latencies):7.2f} ms" if len(latencies) > 1 else "  标准差:   N/A")
        else:
            print("未找到 google_adk schema 中的表")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"表查询测试失败: {e}")

    return latencies

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Supabase 数据库延迟测试")
    print("="*60)
    print(f"数据库: db.jmuqxmdtwjpibskpyaxk.supabase.co")
    print(f"Schema: google_adk")

    # 运行所有测试
    test_connection_latency(10)
    test_query_latency(10)
    test_ping_latency(10)
    test_table_query_latency(5)

    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}\n")

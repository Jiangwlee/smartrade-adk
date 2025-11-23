#!/usr/bin/env python3
"""检查 Supabase 数据库位置和网络信息"""

import psycopg2
import socket

DB_URL = "postgresql://postgres:IURSG6o3wEsQKHiN@db.jmuqxmdtwjpibskpyaxk.supabase.co:5432/postgres?options=-csearch_path%3Dgoogle_adk"

def get_database_location():
    """查询数据库的地理位置信息"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()

        print("="*60)
        print("数据库信息")
        print("="*60)

        # 获取数据库版本
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"\n数据库版本: {version}")

        # 获取服务器时区
        cursor.execute("SHOW timezone")
        timezone = cursor.fetchone()[0]
        print(f"服务器时区: {timezone}")

        # 获取当前时间
        cursor.execute("SELECT NOW()")
        current_time = cursor.fetchone()[0]
        print(f"服务器时间: {current_time}")

        # 尝试获取 IP 地址
        host = "db.jmuqxmdtwjpibskpyaxk.supabase.co"
        try:
            ip_address = socket.gethostbyname(host)
            print(f"\n数据库 IP: {ip_address}")
        except socket.gaierror:
            print(f"\n无法解析域名: {host}")

        # 检查是否有地理位置扩展
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_available_extensions
                WHERE name = 'postgis'
            )
        """)
        has_postgis = cursor.fetchone()[0]
        print(f"PostGIS 扩展: {'已安装' if has_postgis else '未安装'}")

        # 查看当前 schema
        cursor.execute("SELECT current_schema()")
        schema = cursor.fetchone()[0]
        print(f"当前 Schema: {schema}")

        # 查看连接信息
        cursor.execute("""
            SELECT
                inet_client_addr() as client_ip,
                inet_server_addr() as server_ip,
                inet_server_port() as server_port
        """)
        conn_info = cursor.fetchone()
        print(f"\n连接信息:")
        print(f"  客户端 IP: {conn_info[0]}")
        print(f"  服务端 IP: {conn_info[1]}")
        print(f"  服务端端口: {conn_info[2]}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    get_database_location()

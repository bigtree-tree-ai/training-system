"""训练分析系统 — 统一CLI入口"""
import sys


def main():
    if len(sys.argv) < 2:
        print("用法: python3 main.py <命令>")
        print("  import-csv     从CSV冷启动导入")
        print("  import-fit     批量扫描FIT文件导入")
        print("  analyze        计算所有分析指标")
        print("  warnings       检查训练预警")
        print("  ai macro [days]    AI宏观训练回顾(默认30天)")
        print("  ai session <id>    AI单次训练点评")
        print("  serve          启动Web服务")
        return

    cmd = sys.argv[1]

    if cmd == 'import-csv':
        from data_import.csv_importer import import_csv
        import_csv()

    elif cmd == 'import-fit':
        reparse = '--reparse-all' in sys.argv
        from data_import.batch_import import scan_and_import
        scan_and_import(reparse_all=reparse)

    elif cmd == 'analyze':
        from analysis.session_metrics import compute_all_session_metrics
        from analysis.macro_metrics import compute_daily_load
        from analysis.weekly_summary import compute_weekly_summaries
        print("=== Step 1: Session指标 ===")
        compute_all_session_metrics()
        print("\n=== Step 2: 每日负荷 + PMC ===")
        compute_daily_load()
        print("\n=== Step 3: 周汇总 ===")
        compute_weekly_summaries()

    elif cmd == 'warnings':
        from analysis.trend_detector import print_warnings
        print_warnings()

    elif cmd == 'ai':
        from ai_coach.coach import macro_review, session_review
        if len(sys.argv) < 3:
            print("用法: python3 main.py ai macro [days] | ai session <id>")
            return
        sub = sys.argv[2]
        if sub == 'macro':
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            print(macro_review(days=days))
        elif sub == 'session':
            if len(sys.argv) < 4:
                print("请指定session_id")
                return
            print(session_review(int(sys.argv[3])))
        else:
            print(f"未知AI子命令: {sub}")

    elif cmd == 'serve':
        import uvicorn
        port = 8080
        if '--port' in sys.argv:
            idx = sys.argv.index('--port')
            port = int(sys.argv[idx + 1])
        print(f"启动Web服务: http://localhost:{port}")
        uvicorn.run("web.app:app", host="0.0.0.0", port=port, reload=True)

    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()

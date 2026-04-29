from scripts import api
from scripts import mailme
from pathlib import Path

def main():
    try:
        # api.get_DocsList()
        # mailme.send_email_abount_accomplish(
        #     additional_info = f"DocsListのダウンロードが完了しました。{len(list(Path('./docsList').glob('*.csv')))}件のDocsListがダウンロードされました。"
        # )
        api.get_doc(date_from='2016-02-19')
        mailme.send_email_abount_accomplish(
            additional_info = f"Docのダウンロードが完了しました。{len(list(Path('./downloaded_docs').glob('*.zip')))}件のDocがダウンロードされました。"
        )
    except Exception as e:
        print(f"An error occurred: {e}")
        mailme.send_email_abount_error(e)
    finally:
        print("処理が完了しました。")

if __name__ == "__main__":
    main()

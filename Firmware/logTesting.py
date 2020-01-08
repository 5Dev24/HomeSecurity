from src.logging import Log, LogType

Log(LogType.Info, input("Msg for info log: ")).post()
Log(LogType.Warn, input("Msg for warn log: ")).post()

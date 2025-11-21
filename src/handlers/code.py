from aiogram import Router


router = Router()
# code (всем): показать текущий код чата (как текст, c Markdown-кодблоком).
# code_completed (админ): “доделать” код до компилируемого (через LLM) без добавления новой логики; вернуть текст и файл.

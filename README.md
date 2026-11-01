# doc-kit

Создаёт проект документации и закрепляет версии инструментов.

```
python tools/kit.py init acme --dir D:/projects --github
```

Команда создаёт `acme-docs`, ставит BMAD из приватного `BMAD-METHOD`, а также `doc-architecture` и `doc-gates` тех версий, что указаны в `versions.yaml`. Опция `--github` создаёт приватный репозиторий.

Обновление инструмента в проекте: измените строку в `doc.lock.yaml` и выполните `python tools/kit.py sync --root acme-docs`.

Нужны Python 3.10+, Node.js, Git, uv и доступ к приватному `BMAD-METHOD`. BMAD Method является товарным знаком BMad Code, LLC. Этот проект с ним не связан.

Полный сценарий описан в [doc-rules](https://github.com/DemonIngvi/doc-rules/blob/main/docs/new-project.md).

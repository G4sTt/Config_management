# Граф зависимостей Cargo

Практическая работа № 2 по конфигурационному управлению, вариант 13.
Приложение написано на Python со стандартной библиотекой.

## Быстрый запуск

Откройте папку Conf_2 в PyCharm и выберите Python 3.10 или новее.
В терминале проекта выполните:

```powershell
.\run.bat test
.\run.bat demo
.\run.bat analyze configs/simple.ini
.\run.bat analyze configs/reverse.ini --stage reverse
```

Для этих команд достаточно Python. Они работают с локальными данными.
Настройка виртуального окружения .venv поддерживается скриптом запуска.
Сторонние Python-пакеты в requirements.txt отсутствуют.

## Конфигурация

Настройки читаются из раздела analysis файла INI.

| Ключ | Значение |
| --- | --- |
| package | Имя пакета или name@version. В тестовом режиме используются A, B, C и другие имена из заглавных латинских букв. |
| repository | URL sparse-индекса Cargo либо путь к JSON тестового репозитория. |
| test_mode | true для локального JSON, false для HTTP-репозитория. |
| ascii_tree | Включает текстовое дерево. |
| max_depth | Максимальная глубина. Корень имеет глубину 0. |

Относительный путь repository вычисляется от папки файла INI.
Пример первого этапа:

```powershell
python src/main.py --config configs/simple.ini --stage config
$env:PYTHONPATH = "src"
python -B -m unittest discover -s tests -v
```

Все пять значений проверяются до анализа зависимостей.

## Сбор данных Cargo

Прямые зависимости загружаются через urllib из sparse-индекса Cargo.
Готовые менеджеры пакетов и библиотеки получения зависимостей в анализаторе
не используются. При выборе версии учитываются ограничения SemVer и yanked.
Граф включает обязательные зависимости kind=normal для всех платформ.
Необязательные, build- и dev-зависимости исключены. Полный выбор features
и глобальное согласование версий Cargo находятся за пределами этой модели.

```powershell
python src/main.py --config configs/itoa.ini --stage direct
```

## Рекурсивный BFS

Алгоритм visit_level обрабатывает весь текущий слой и передаёт следующий
слой рекурсивному вызову. Глубина корня равна 0, глубина прямых зависимостей
равна 1. Узлы на предельном слое включаются в граф без раскрытия потомков.
Посещённые пакеты учитываются по имени и версии. Рёбра циклов сохраняются,
а повторная обработка уже посещённых узлов прекращается.

Тестовый репозиторий представляет собой JSON с полным списком узлов.
Каждому имени сопоставлен массив его прямых зависимостей.

```powershell
python src/main.py --config configs/simple.ini
python src/main.py --config configs/cycle.ini
python src/main.py --config configs/depth_one.ini
```

## Обратные зависимости

Режим reverse использует тот же рекурсивный BFS с функцией поиска пакетов,
которые зависят от текущего. Для локального репозитория рассматривается
весь JSON, включая пакеты вне исходного прямого графа.
Для сетевого режима используется API reverse_dependencies, если его
поддерживает выбранный реестр. Список зависит от полноты и актуальности API.

```powershell
python src/main.py --config configs/reverse.ini --stage reverse
```

Для B прямые потребители — A и C, транзитивные — D и E.
В представлении обратного графа стрелка B -> A означает, что A зависит от B.

## Визуализация

Основной режим graph печатает описание Graphviz DOT в stdout.
ASCII-дерево при ascii_tree=true выводится отдельно в stderr. Это позволяет
перенаправлять stdout в корректный DOT-файл. Ключ --output сохраняет DOT
в UTF-8 независимо от настроек кодировки PowerShell.

```powershell
.\run.bat analyze configs/simple.ini --output build/simple.dot
.\run.bat analyze configs/cycle.ini
.\run.bat analyze configs/depth_one.ini
.\run.bat analyze configs/isolated.ini
.\run.bat analyze configs/simple.ini --stage direct
.\run.bat analyze configs/simple.ini --stage config
```

Меткой [cycle] обозначается возврат к предку текущей ветви,
[seen] — повторное отображение ранее раскрытого узла,
[depth limit] — остановка раскрытия из-за выбранной глубины.
Для преобразования DOT в картинку можно использовать Graphviz:

```powershell
dot -Tsvg build/simple.dot -o build/simple.svg
```

В архив проекта включены готовые SVG в build/previews. Их можно открыть
в браузере. Программа получает зависимости через собственный HTTP-код,
а Graphviz используется для отображения полученного DOT.

## Три реальных пакета

Для сетевого анализа выполните:

```powershell
.\run.bat live
```

Примеры используют itoa@1.0.15, num-integer@0.1.46 и itertools@0.13.0.
В build сохраняются DOT и ASCII-деревья. Версия корня закреплена в INI,
версии транзитивных зависимостей выбираются по актуальному sparse-индексу.
На момент проверки получены графы:

```text
itoa@1.0.15
num-integer@0.1.46 -> num-traits@0.2.19
itertools@0.13.0 -> either@1.19.0
```

itoa является примером пакета без обязательных normal-зависимостей.

## Сравнение с Cargo

Для самостоятельного повторения этого пункта установите Rust через rustup
с официальной страницы https://rust-lang.org/tools/install/ и перезапустите
терминал. Проверьте доступность инструментов и запустите сравнение:

```powershell
cargo --version
rustc --version
.\run.bat compare
```

Модуль comparison.py создаёт отдельные Cargo.toml и вызывает cargo tree.
Эта команда используется для независимой проверки. Основные модули
registry.py и analysis.py получают данные напрямую из HTTP-репозитория.
Для проверки уже использованы Cargo 1.85.1 и rustc 1.85.1.
Три сравнения завершились MATCH. В build/comparison/results.json и
build/comparison/*/cargo-tree.txt сохранены фактические результаты.

Используются параметры cargo tree --edges normal --target all --prefix depth
--charset ascii --no-dedupe. В manifest отключены default-features.
Проверяются и узлы с версиями, и направленные рёбра.
Результат относится к указанным трём примерам и выбранной модели.

Cargo самостоятельно согласует версии и активирует зависимости через features.
В этом анализаторе каждое ребро разрешается независимо, optional-зависимости
исключаются, а зависимости всех target-платформ объединяются. Поэтому
для произвольных пакетов возможны отличия от cargo tree. Различия объясняются
выбором features, глобальным разрешением версий и фильтрацией kinds/targets.

## Структура и проверка

| Модуль | Назначение |
| --- | --- |
| settings.py | Чтение INI и проверка пяти параметров |
| versions.py | Сравнение версий и диапазонов Cargo |
| registry.py | Собственный HTTP-клиент sparse-индекса |
| repositories.py | Проверка локальных JSON-графов |
| graph.py | Рекурсивный BFS с глубинами и посещёнными узлами |
| analysis.py | Соединение репозитория с обходом |
| visualize.py | Graphviz DOT и ASCII-дерево |
| main.py | CLI и обработка ошибок |
| demo.py | Локальные и сетевые примеры |
| comparison.py | Отдельное сравнение с cargo tree |

Набор unittest содержит 28 тестов конфигурации, SemVer, HTTP-ошибок,
графов, обратных зависимостей, CLI и представлений графа.
Тесты не обращаются к сети и запускаются командой run.bat test.
При ошибке CLI завершает работу с кодом 2.
Глубина рекурсии ограничена возможностями интерпретатора Python.
Для очень глубоких графов уменьшите max_depth.

Пять этапов разработки сохранены отдельными коммитами.
Каталог build исключён из Git. Его результаты пересоздаются командами demo,
live и compare. Для сдачи опубликуйте локальный репозиторий в Git-сервисе.

## Источники

Задание — сборник практических работ № 2 по конфигурационному управлению,
ИКБО-12-25, РТУ МИРЭА, 2026, вариант 13, страницы 44–46.

- Формат индекса https://doc.rust-lang.org/cargo/reference/registry-index.html
- Диапазоны версий https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html
- Сравнение https://doc.rust-lang.org/cargo/commands/cargo-tree.html
- Язык DOT https://graphviz.org/doc/info/lang.html

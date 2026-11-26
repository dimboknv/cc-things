# planning объявляет свои зависимости и рисует развилки через diagram-design

## Goal

Плагин planning сам объявляет плагины, без которых он не работает. При установке Claude Code ставит их автоматически или сразу говорит, чего не хватает: сейчас об этом узнают посреди прогона. Бинарники и рецепт mailbox-chat по-прежнему проверяются там, где их вызывают, а README перечисляет всё внешнее с командами установки. Запуск пира отказывается, если у Claude нет скилла mailbox-chat. На развилках brainstorm ведущий отдаёт содержание картинки diagram-design, и тот сам выбирает тип; поток «кто кого зовёт» рисует страница, а форму, для которой у diagram-design нет типа, ведущий рисует руками. Картинку diagram-design `fork.py` вшивает в карточку на всю её ширину, тёмную, с системными шрифтами. Общие правила вызова diagram-design лежат в одном файле, его может прочитать любой скилл planning.

До: в манифесте нет зависимостей, brainstorm ссылается на необъявленный thinking-tools, все картинки развилок рисует страница или ведущий руками. После: три объявленные зависимости, ссылок на необъявленные скиллы нет, картинки развилок, кроме потоков и экранов, рисует diagram-design.

Closes: nothing — инструментарий плагина, требований и задач в трекере нет.

## Owner Sign-off

- Зависимости жёсткие. Пользователь planning должен заранее добавить marketplace `umputun/revmux`, `umputun/revdiff` и `cathrynlavery/diagram-design`. Иначе planning ставится, но не загружается целиком, даже brainstorm. Каждый пользователь planning получает revdiff и diagram-design, даже если exec-plan ему не нужен.
- Пины версий не ставятся: обновление revmux, revdiff или diagram-design приходит в planning без проверки.
- Картинки diagram-design всегда тёмные («по умолчанию рисовать тёмную, так как это в терминале всё»). Это снимает решение брейншторма «тема по терминалу»: на светлой теме agterm картинка будет тёмным прямоугольником.
- Правило, которое снимает две паузы diagram-design (вопрос про стиль и подтверждение плана), держится на тексте его скилла. После обновления diagram-design первая развилка с картинкой может снова спросить про стиль. Тогда правится общий файл правил.
- Выпуск новой версии planning (поле `version` и отдельный коммит релиза) делает владелец, вне прогона.

## Decisions

**D1. Зависимости объявлены в манифесте planning, чужие marketplace — в allowlist.** В `dependencies` плагина planning записаны `revmux@revmux`, `revdiff@revdiff` и `diagram-design@diagram-design` в строковой форме, без версий. В `allowCrossMarketplaceDependenciesOn` нашего marketplace перечислены эти три marketplace. Причина: это документированный механизм Claude Code, и отсутствие зависимости видно при установке. Отвергнуто: перевыставлять чужие плагины в нашем marketplace (вторая копия под нашим именем, мы становимся зеркалом чужих релизов) и проверка скриптом без автоустановки (ничего не ставится само). Пины отвергнуты: теги revmux вида `v0.3.0`, а не `revmux--v…`, и на локальном marketplace пин не соблюдается.

**D2. Ссылок на необъявленные скиллы нет.** Шаг исследования brainstorm предлагает только Explore-агентов. Упоминание `thinking-tools:ask-codex` и `thinking-tools:dialectic` уходит. Отвергнуто: объявить thinking-tools зависимостью — ради одной строки-подсказки он тянул бы целый чужой каталог umputun/cc-thingz.

**D3. Бинарники и mailbox-chat проверяются там, где их вызывают; README перечисляет всё внешнее.** Для каждого бинарника (`revmux`, `revdiff`, `codex`, `claude`, `agtermctl` вместе с приложением agterm, `mailbox-chat.py`, `python3`) README говорит, зачем он нужен, как его поставить и что будет без него. Для mailbox-chat README ссылается на шаги кукбука agterm `two-agent-mailbox-chat`. Отвергнуто: общий скрипт проверки на старте каждого скилла (дублирует проверки на месте) и SessionStart-хук (шум в каждой сессии); упаковка mailbox-chat в плагин (половину установки — Codex, песочницу, `hooks.conf` agterm — плагин всё равно не ставит).

**D4. Запуск пира отказывается, если у Claude нет скилла mailbox-chat.** Ведущий и пир-Claude загружают скилл `mailbox-chat` первым шагом. Скрипт запуска пира уже проверяет хуки Claude и скилл у Codex, а скилл у Claude не проверяет. Проверка смотрит в папку скиллов конфигурации Claude и в `.claude/skills` проекта, так же, как поиск хука смотрит в настройки обоих мест. Отвергнуто: ничего не менять — без скилла чат рушится на первом сообщении, а не при запуске.

**D5. Правила вызова diagram-design — файл `plugins/planning/references/diagrams.md`.** Он лежит рядом с правилом закрытого вопроса:
- кто рисует: поток «кто кого зовёт» рисует страница развилки; всё остальное ведущий сначала отдаёт diagram-design — роли, что меняется, вопрос развилки — и тот сам выбирает тип. Если diagram-design ответил, что подходящего типа нет (так будет с наброском экрана), ведущий рисует руками SVG, как сегодня;
- как его загрузить: под любым из двух имён, `diagram-design:diagram-design` (плагин) или `diagram-design` (голый скилл); ведущий запоминает папку скилла, которую печатает загрузка;
- как ответить на обе его паузы: стиль стандартный, рисовать без подтверждения, строку плана записать в чат;
- что просить: тёмный вариант, один файл;
- одна картинка на развилку: сначала рисуется «сегодня», каждый вариант — его копия, где отмечено новое и ушедшее, а не новая картинка;
- как картинка попадает на страницу: ссылка на разметку `page.md`.

Файл написан так, что другой скилл подключается одной строкой. Сейчас его читает только brainstorm. Отвергнуто: правила внутри brainstorm (их пришлось бы копировать в make-plan и exec-plan); ведущий сам решает, что экран рисует он (тип за diagram-design выбирал бы ведущий); diagram-design рисует экран ближайшим типом (получается схема вложенности, а не экран).

**D6. `fork.py` превращает рисунок diagram-design в SVG его же `export_svg.py` и вшивает как `<img>` с data-URI.** Фрагмент ссылается на HTML-файл diagram-design, ведущий передаёт `fork.py` папку скилла. `export_svg.py` из этой папки переносит стили страницы внутрь SVG и добавляет к id в `<defs>` префикс. `fork.py` кладёт результат в страницу картинкой, а страница по-прежнему открывается без доступа к файлам. Отвергнуто: вырезать `<svg>` из HTML самим (рисунки со стилями на классах теряют стиль внутри `<img>`), вставлять `<svg>` прямо в разметку (стиль страницы `svg text { font: 12px … }` перебивает подписи), `<iframe srcdoc>` (тянет всю страницу, диаграмма обрезается), открытие страницы с `--cwd` (страница перестаёт быть самодостаточной), поиск папки скилла самим `fork.py` (путь меняется с версией и способом установки).

**D7. Картинка diagram-design всегда тёмная.** diagram-design рисует своим тёмным шаблоном. Тёмной копии и выбора варианта по теме нет. Причина: в терминале всё тёмное, а один прогон без правил замены цветов — самое простое. Отвергнуто: светлая картинка плюс тёмная копия по правилам цветов diagram-design (правила повторяют чужие, а одной таблицы ролей мало); второй прогон на тёмный вариант (вдвое больше прогонов); тёмная по умолчанию со светлой копией для светлой темы (те же правила в обратную сторону).

**D8. `fork.py` заменяет шрифты diagram-design на системные стеки.** Внутри `<img>` SVG не грузит внешние шрифты, а голый `monospace` в WebKit — это Courier с засечками. Заменяются все написания семейств Geist Mono, Geist и Instrument Serif: в кавычках и без, с пробелами и без, в атрибутах `font-family` и в стилях внутри SVG, в том числе в сокращённом `font:`. Моно-стек — `ui-monospace, 'SF Mono', Menlo, monospace`, sans — `system-ui, -apple-system, sans-serif`, serif — `ui-serif, Georgia, serif`. Отвергнуто: флаг `--system-fonts` у `export_svg.py` — он только убирает импорт Google Fonts, а имена семейств оставляет.

**D9. Картинка diagram-design занимает всю ширину карточки, текст идёт под ней; такая развилка показывается раскладкой `rows`.** При 3/5 ширины в `rows` картинка 820 px шириной ужимается до 614 px, и подписи стрелок становятся около 6 px. В колонке шириной 330 px она не читается вовсе. Отвергнуто: картинка в левой колонке, как у рисунков страницы.

## Premises

- В манифесте planning нет зависимостей: `rg -c dependencies plugins/planning/.claude-plugin/plugin.json` ничего не выводит.
- В нашем marketplace нет allowlist: `rg -c allowCrossMarketplaceDependenciesOn .claude-plugin/marketplace.json` ничего не выводит.
- Документация Claude Code, code.claude.com/docs/en/plugins/dependencies.md: "Each entry is `\"name\"`, `\"name@marketplace\"`, or `{ \"name\": \"...\", \"marketplace\": \"...\", \"version\": \"...\" }`" и `"allowCrossMarketplaceDependenciesOn": ["your-shared-marketplace"]`.
- Поведение зависимостей проверено на двух локальных marketplace в отдельном `CLAUDE_CONFIG_DIR`:
  - чужой marketplace не добавлен — `claude plugin install main@ours-mkt` → `Warning: dependency "dep@theirs-mkt" was not installed (no marketplace you have added lists it). "main" will not load without it`;
  - marketplace добавлен, allowlist есть — `(+ 1 dependency: dep)`;
  - allowlist нет — `claude plugin list` → `Error: Dependency "dep@theirs-mkt" is not installed`.
- Имена marketplace и плагинов: `"name": "revmux"`, `"name": "revdiff"`, `"name": "diagram-design"` в `~/.claude/plugins/marketplaces/{revmux,revdiff,diagram-design}/.claude-plugin/marketplace.json`.
- Манифесты проверяются: `claude plugin validate plugins/planning` → `✔ Validation passed`.
- brainstorm ссылается на необъявленный плагин: `plugins/planning/skills/brainstorm/SKILL.md` — "`thinking-tools:ask-codex`".
- README говорит только про agterm и revmux: `README.md` — "The skills assume agterm for the fork page, the peer and the".
- exec-plan уже проверяет бинарники ревью на месте: `plugins/planning/skills/exec-plan/SKILL.md` — "the review tools, `revmux`, `claude` and `codex` on `PATH`".
- Скрипт запуска пира проверяет хук Claude и скилл у Codex, но не скилл у Claude: `plugins/planning/skills/brainstorm/scripts/peer.sh` — "grep -qs 'mailbox-chat.py claude-hook'" и "[ -f \"$codex_home/skills/mailbox-chat/SKILL.md\" ]".
- Скрипт запуска пира вызывает `agtermctl` по имени из `PATH`, а не через `AGTERMCTL`: там же — "command -v agtermctl >/dev/null || refuse".
- Пир-Claude загружает скилл mailbox-chat: `plugins/planning/skills/brainstorm/peer.md` — "1. Load the `mailbox-chat` skill."; так же `plugins/planning/skills/exec-plan/references/peer.md`.
- `fork.py` открывает страницу без доступа к файлам: `plugins/planning/skills/brainstorm/scripts/fork.py` — `"--chromeless",` без `--cwd`. Справка agterm: "Without --cwd, the page has no file access" (`agtermctl session overlay open --help`).
- Стиль страницы ломает встроенный SVG: `plugins/planning/skills/brainstorm/assets/fork.html` — "svg text { font: 12px system-ui, sans-serif; fill: var(--fg); }".
- Раскладка `rows` даёт картинке 3/5 ширины: там же — ".rows .opt .split { display: grid; grid-template-columns: 3fr 2fr;".
- Картинка блока — его первый элемент, рисунок или `<svg>`: там же — "first.tagName === 'FIGURE'".
- Сегодня экран и прочие формы ведущий рисует руками: `plugins/planning/skills/brainstorm/page.md` — "**Anything else**, states, a place where data lives, the user's screen, is an inline".
- Загрузка скилла печатает его папку: вывод Skill в этой сессии — "Base directory for this skill: /Users/dmitry/.claude/skills/diagram-design".
- У diagram-design есть экспорт в самостоятельный SVG без сторонних зависимостей: `<папка скилла>/scripts/export_svg.py` — "Export a diagram HTML file to a standalone, inline-safe SVG." и "No third-party deps."
- У diagram-design есть тёмный шаблон: `<папка скилла>/assets/template-dark.html`.
- Типа «экран» у diagram-design нет: `rg -i 'wirefram|mockup'` по `<папка скилла>/SKILL.md` и `<папка скилла>/references` пуст.
- Шрифты в SVG diagram-design без системного стека: `<папка скилла>/assets/example-architecture.html` — `font-family="'Geist Mono', monospace"`.
- Паузы diagram-design: `<папка скилла>/SKILL.md` — "verify the style guide has been customized" и "Skip the pause only when".
- `<img>` с SVG в data-URI грузится в WebKit agterm: страница-проба через `agtermctl session overlay open --html <проба> --chromeless --js --block` вернула `"complete":true,"naturalWidth":300,"naturalHeight":146,"shownWidth":614,"viewport":1141`.

## Contracts and Data

- **Фрагмент fork-страницы** (разметка в `plugins/planning/skills/brainstorm/page.md`, раздел «Pictures»): появляется элемент картинки, который ссылается на HTML-файл diagram-design. Владелец формы — `page.md`. Читают `fork.py` (экспорт, шрифты, вшивание) и `assets/fork.html` (раскладка на всю ширину). Пишет ведущий brainstorm по `SKILL.md` и `references/diagrams.md`. Старые формы (`data-flow`, `<figure>`, `<svg>`) остаются как есть. Меняет задача «fork-страница вшивает тёмные картинки diagram-design».
- **Манифесты плагина** (`plugins/planning/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`): новые поля `dependencies` и `allowCrossMarketplaceDependenciesOn`. Читает Claude Code при установке и загрузке. Меняет задача «planning объявляет зависимости и перечисляет внешнее в README».

## Out of Scope

- Картинки diagram-design в make-plan и на странице статуса exec-plan: подключаются одной строкой к `references/diagrams.md`, когда станет ясно, какая картинка там нужна.
- Светлая картинка на светлой теме: владелец выбрал всегда тёмную.
- Упаковка mailbox-chat в плагин или просьба к umputun выпустить его плагином: решено считать его внешним требованием.
- Плагин `agterm@agterm` как зависимость: planning вызывает `agtermctl` напрямую, без этого скилла.
- Пины версий зависимостей.
- Выпуск новой версии planning — владелец.

## Execution

- **Gate.** В cc-things нет `CLAUDE.md` и файла сборки, поэтому по умолчанию проверка — то, что в проекте есть: каждый `tests/*.sh` зелёный, `ruff check plugins` чистый, `claude plugin validate plugins/planning` и `claude plugin validate .` проходят. Новое поведение скриптов доказывается тестом в `tests/` по образцу существующих: каждая проверка отчитывается, скрипт выходит с ненулевым кодом при любом провале. Стаб `agtermctl` подставляется через `AGTERMCTL` для `fork.py`; для `peer.sh`, который зовёт `agtermctl` по имени, стабы кладутся первыми в `PATH`.
- **Environment.** `claude`, `python3` и `ruff` на `PATH`. Установленный diagram-design в тестах не нужен: тест кладёт свою папку скилла с маленьким `scripts/export_svg.py`-стабом и свой HTML.
- **Barriers.** Нет.
- **Skills.** `skill-creator` для правок `SKILL.md` и справочных файлов скиллов.
- **Shared files.**

| Файл | Задачи | Вторая |
|---|---|---|
| `plugins/planning/skills/brainstorm/SKILL.md` | «planning объявляет зависимости и перечисляет внешнее в README», «общие правила картинок diagram-design и их место в brainstorm» | «общие правила картинок diagram-design и их место в brainstorm» |
| `plugins/planning/skills/brainstorm/page.md` | «fork-страница вшивает тёмные картинки diagram-design», «общие правила картинок diagram-design и их место в brainstorm» | «общие правила картинок diagram-design и их место в brainstorm» |

## Implementation Steps

### Task 1: planning объявляет зависимости и перечисляет внешнее в README

Result: манифест planning объявляет revmux, revdiff и diagram-design. Наш marketplace разрешает их три marketplace. В brainstorm нет ссылок на thinking-tools. README перед установкой planning даёт три `marketplace add`, перечисляет бинарники с командами установки и последствиями их отсутствия и ссылается на кукбук `two-agent-mailbox-chat`.

Decision: D1, D2, D3.

Where: `.claude-plugin/`, `plugins/planning/.claude-plugin/`, `plugins/planning/skills/brainstorm/`, `README.md`.

- [ ] `dependencies` в манифесте planning и allowlist в манифесте marketplace
- [ ] шаг исследования brainstorm предлагает только Explore-агентов
- [ ] README: раздел установки с тремя `marketplace add` до установки planning; список бинарников и mailbox-chat по D3
- [ ] acceptance: `python3 -c "import json; d=json.load(open('plugins/planning/.claude-plugin/plugin.json')); assert {'revmux@revmux','revdiff@revdiff','diagram-design@diagram-design'} <= set(d.get('dependencies', []))"` и `python3 -c "import json; d=json.load(open('.claude-plugin/marketplace.json')); assert {'revmux','revdiff','diagram-design'} <= set(d.get('allowCrossMarketplaceDependenciesOn', []))"` проходят; `claude plugin validate plugins/planning` и `claude plugin validate .` проходят
- [ ] acceptance: `rg -n -i 'thinking.?tools|ask-codex|dialectic' plugins README.md` пуст
- [ ] acceptance: `rg -n 'marketplace add (umputun/revmux|umputun/revdiff|cathrynlavery/diagram-design)' README.md` находит все три; `rg -n 'two-agent-mailbox-chat' README.md` находит; `for b in revmux revdiff codex claude agtermctl mailbox-chat.py python3; do rg -q -F "$b" README.md || echo "missing $b"; done` ничего не печатает

### Task 2: запуск пира отказывается без скилла mailbox-chat у Claude

Result: скрипт запуска пира отказывается с понятной причиной, если скилла `mailbox-chat` нет ни в папке скиллов конфигурации Claude, ни в `.claude/skills` проекта. Тест в `tests/` доказывает отказ и то, что при наличии скилла эта проверка пройдена.

Decision: D4.

Where: `plugins/planning/skills/brainstorm/scripts/`, `tests/`.

- [ ] проверка скилла Claude рядом с проверкой хука Claude, для обоих видов пира
- [ ] тест: стабы `agtermctl` и `mailbox-chat.py` первыми в `PATH`, временная `CLAUDE_CONFIG_DIR` с хуком в настройках; без скилла — отказ с его названием, со скиллом — эта проверка пройдена
- [ ] acceptance: `rg -l 'peer\.sh' tests` находит тест; каждый `tests/*.sh` зелёный

### Task 3: fork-страница вшивает тёмные картинки diagram-design

Result: фрагмент развилки может сослаться на HTML-файл diagram-design. `fork.py` с переданной папкой скилла прогоняет файл через её `scripts/export_svg.py`, заменяет шрифты на системные стеки и вшивает SVG как `<img>` с data-URI. Страница показывает такую картинку на всю ширину карточки, текст под ней. Развилка с такой картинкой идёт раскладкой `rows`. Разметка и вызов описаны в `page.md`. Тест в `tests/` доказывает экспорт через скрипт из переданной папки, вшивание, замену всех написаний шрифтов и ошибку, если ссылка есть, а папки скилла нет.

Decision: D6, D8, D9.

Where: `plugins/planning/skills/brainstorm/scripts/`, `plugins/planning/skills/brainstorm/assets/`, `plugins/planning/skills/brainstorm/page.md`, `tests/`.

- [ ] `fork.py`: экспорт через `export_svg.py` переданной папки, замена шрифтов по D8, вшивание data-URI; ошибка с понятной причиной, если ссылка есть, а папки скилла или скрипта нет
- [ ] `fork.html`: картинка diagram-design на всю ширину карточки с текстом под ней, раскладка `rows`
- [ ] `page.md`: элемент картинки diagram-design, как передать папку скилла, что делает `fork.py`
- [ ] тест со стабом `agtermctl` и своей папкой скилла, где стаб `export_svg.py` выдаёт SVG со шрифтами в разных написаниях (в кавычках и без, в атрибуте и в `<style>`, в сокращённом `font:`): в собранной странице картинка в data-URI, в декодированном SVG нет ни одного имени Geist, Geist Mono и Instrument Serif; без папки скилла — ошибка
- [ ] acceptance: `rg -l 'fork\.py' tests` находит тест; каждый `tests/*.sh` зелёный; `ruff check plugins` чистый

### Task 4: общие правила картинок diagram-design и их место в brainstorm

Result: `plugins/planning/references/diagrams.md` описывает правила по D5 и D7. Раздел fork-страницы в `SKILL.md` brainstorm и раздел «Pictures» в `page.md` ссылаются на него и говорят, кто рисует какую форму: поток — страница, остальное — diagram-design, а если у него нет типа — ведущий руками.

Decision: D5, D7.

Where: `plugins/planning/references/`, `plugins/planning/skills/brainstorm/`.

After: «fork-страница вшивает тёмные картинки diagram-design» (правила ссылаются на разметку и вызов, которые та задача описывает в `page.md`, и обе правят `page.md`); «planning объявляет зависимости и перечисляет внешнее в README» (обе правят `SKILL.md` brainstorm).

- [ ] `references/diagrams.md`: кто рисует и запасной путь при отказе, загрузка под обоими именами и запоминание папки скилла, ответы на обе паузы, тёмный вариант, «сегодня» и варианты как копии, ссылка на разметку `page.md`
- [ ] `SKILL.md` brainstorm, раздел «The fork page», и `page.md`, раздел «Pictures»: кто рисует какую форму, со ссылкой на `references/diagrams.md`
- [ ] acceptance: `rg -n 'diagram-design:diagram-design' plugins/planning/references` находит; `rg -n 'references/diagrams\.md|diagrams\.md' plugins/planning/skills/brainstorm/SKILL.md plugins/planning/skills/brainstorm/page.md` находит в обоих файлах

## Post-Completion

- Развилка brainstorm с картинкой состояния в agterm: картинка тёмная, на всю ширину карточки, шрифты без засечек, подписи читаются.
- Развилка с наброском экрана: diagram-design отказывается, ведущий рисует руками.
- Свежая установка planning в отдельном `CLAUDE_CONFIG_DIR` по README: три `marketplace add`, затем `/plugin install planning@dimboknv-cc-things` — зависимости ставятся сами.
- Выпуск новой версии planning.

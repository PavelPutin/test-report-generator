import cutie
from enum import Enum
import os
import datetime
import pandas as pd
import configparser
from markdown_pdf import MarkdownPdf, Section

class HumanReadableEnum(Enum):
  def __new__(cls, *args):
    value = len(cls.__members__) + 1
    obj = object.__new__(cls)
    obj._value_ = value
    return obj

  def __init__(self, human_readable = 'unknown'):
    self.human_readable = human_readable


class Priority(HumanReadableEnum):
  IMMEDIATELY = 'Исправить немедленно'
  AS_SOON_AS_POSSIBLE = 'Исправить как можно быстрее'
  FIX_FOR_RELEASE = 'Исправить к релизу'
  FIX_WHEN_HAVE_TIME = 'Исправить, если будет время'

  
class Severity(HumanReadableEnum):
  BLOCKING = 'Блокирующий'
  CRITICAL = 'Критический'
  IMPORTANT = 'Важный'
  ORDINARY = 'Обычный'
  TRIVIAL = 'Тривиальный'


class Status(HumanReadableEnum):
  BUG = 'Баг'
  INCIDENT = 'Инцидент'
  FEATURE = 'Фича'


class BugReport:
  id: int
  author: str
  creation_datetime: datetime.datetime
  section: str
  type: str
  brief: str
  expected: str
  actual: str
  reproduction_steps: list[str]
  status: Status
  priority: Priority
  seveirty: Severity

  def __str__(self):
    result = ""
    result += f'# Инцидент {self.id}: {self.brief}\n\n'
    result += f'**Приоритет:** {self.priority.human_readable}\n\n'
    result += f'**Важность:** {self.seveirty.human_readable}\n\n'
    result += f'**Статус:** {self.status.human_readable}\n\n'
    result += f'**Где находится:** {self.section}\n\n'
    result += f'**Тип:** {self.type}\n\n'
    result += f'**Время обнаружения**: {self.creation_datetime}\n\n'
    result += f'**Автор:** {self.author}\n\n'
    result += '-' * 20 + '\n\n'
    result += f'## Ожидание\n\n'
    result += f'{self.expected}\n\n'
    result += f'## Реальность\n\n'
    result += f'{self.actual}\n\n'
    result += f'## Шаги воспроизведения\n\n'
    if len(self.reproduction_steps) != 0:
      for i, value in enumerate(self.reproduction_steps):
        result += f'{i + 1}. {value}\n'
      result += '\n'
    else:
      result += f'Шаги воспроизведения не указаны! Сообщите {self.author}\n\n'
    return result


def main():
  config = init_from_ini()
  author = config['core']['author']
  xlsx = config['core']['xlsx']
  output_md = config['core']['output.md']

  df = init_from_xlsx(xlsx)
  locations = set(df['Местонахождение'])
  types = set(df['Тип'])
  while True:
    try:
      next_id = generate_next_id(df)
      bug_report = prompt_bug_report(next_id, author, locations, types)
      locations.add(bug_report.section)
      types.add(bug_report.type)
      add_bug_report_to_data_frame(df, bug_report)
      output_md_filename = write_to_md_file(bug_report, output_md)
      print(f'Отчёт записан в \'{output_md_filename}\'')
    except KeyboardInterrupt:
      break
  write_to_xlsx_file(df, xlsx)
  compile_to_pdf_report(output_md)


def compile_to_pdf_report(output_md):
  pdf = MarkdownPdf(toc_level=1)
  for file in sorted(os.listdir(output_md)):
    file = os.path.join(output_md, file)
    if not (os.path.isfile(file) and os.path.splitext(file)[1] == '.md' and os.path.basename(file).startswith('BR')):
      continue
    with open(file, 'r') as md:
      text = md.read()
      pdf.add_section(Section(text))
  output_pdf_filename = os.path.join(output_md, 'all_bugs_report.pdf')
  pdf.save(output_pdf_filename)


def add_bug_report_to_data_frame(df, bug_report):
  df.loc[len(df.index)] = [
    bug_report.id,
    bug_report.author,
    bug_report.creation_datetime,
    bug_report.priority.human_readable,
    bug_report.seveirty.human_readable,
    bug_report.status.human_readable,
    bug_report.section,
    bug_report.type,
    bug_report.brief,
    bug_report.expected,
    bug_report.actual,
    '\n'.join([f'{i}. {v}' for i, v in enumerate(bug_report.reproduction_steps)])
  ]


def generate_next_id(df):
  ids = df.get('ID')
  next_id = 1 if len(ids) == 0 else max(ids) + 1
  return next_id


def init_from_ini() -> configparser.ConfigParser:
  config = configparser.ConfigParser()
  with open('.ini', 'r') as ini_file:
    config.read_file(ini_file)
  
  need_changes = False
  if not config.has_section('core'):
    need_changes = True
    config.add_section('core')

  for option, default_value, prompt_label in (
    ('author', os.getlogin(), 'Установите имя:'),
    ('xlsx', os.path.join(os.getcwd(), 'bugs.xlsx'), 'Введите путь до Excel БД:'),
    ('output.md', os.getcwd(), 'Папка для сохранения отчётов')
    ):
    if not config.has_option('core', option) or config.get('core', option) == '':
      need_changes = True
      value = prompt(prompt_label, required=False, default_value=default_value)
      config.set('core', option, value)
  if need_changes:
    with open('.ini', 'w') as ini:
      config.write(ini)
  return config


def init_from_xlsx(xlsx) -> pd.DataFrame:
  if os.path.exists(xlsx):
    df = pd.read_excel(xlsx)
    return df
  else:
    return pd.DataFrame(columns=[
      'ID',
      'Автор',
      'Дата и время нахождения',
      'Приоритет',
      'Важность',
      'Статус',
      'Местонахождение',
      'Тип',
      'Краткое описание',
      'Ожидание',
      'Реальность',
      'Шаги воспроизведения',
    ])


def prompt_bug_report(next_id: int, author: str, locations: set[str], types: set[str]) -> BugReport:
  bug_report = BugReport()
  bug_report.id = next_id
  bug_report.author = author
  print(f'Отчёт о баге c id {bug_report.id}')
  bug_report.creation_datetime = datetime.datetime.now()
  bug_report.brief = prompt_brief()
  bug_report.section = prompt_with_old_variants('Местонахождение инцидента:', locations)
  bug_report.type = prompt_with_old_variants('Тип инцидента:', types)
  bug_report.expected = prompt('Ожидаемый результат:')
  bug_report.actual = prompt('Реальный результат:')
  bug_report.reproduction_steps = prompt_list('Шаги воспроизведения:')
  bug_report.priority = prompt_select('Приоритет:', Priority)
  bug_report.seveirty = prompt_select('Важность:', Severity)
  bug_report.status = prompt_select('Статус', Status)
  return bug_report


def write_to_md_file(bug_report: BugReport, output_dir: str) -> str:
  filename = os.path.join(output_dir, generate_md_filename(bug_report))
  with open(filename, 'w') as output:
    output.write(str(bug_report))
  return filename


def generate_md_filename(bug_report: BugReport) -> str:
  return f'BR-{bug_report.id}-{bug_report.priority.value}{bug_report.seveirty.value}.md'


def write_to_xlsx_file(df: pd.DataFrame, filename: str) -> None:
  df.to_excel(filename, index=False)


def prompt(label: str, required: bool = True, default_value: str = '') -> str:
  if not required and default_value != '':
    label = label.removesuffix(':')
    label = label + f' (По умолчанию {default_value})' + ':'
  print(label, end=" ")
  value = input().strip()
  while required and value == '':
    print_error('Обязательное значение', len(label))
    value = input().strip()
  if value == '' and default_value != '':
    value = default_value
  return value


def prompt_brief() -> str:
  result = prompt('Краткое описание бага:')
  words = result.split()
  if 0 <= len(words) <= 3:
    print_warning('Слишком короткое описание')
  elif 10 < len(words):
    print_warning('Слишком длинное описание')
  return result


def prompt_list(label: str, ordered: bool = True) -> list[str]:
  result: list[str] = []
  print(label)

  list_marker = (lambda : f'{len(result) + 1}.') if ordered else (lambda : '-')
  first = True

  while (value := prompt(list_marker(), first).strip()) != '':
    result.append(value)
    first = False
  return result


def prompt_select(label: str, source_enum: HumanReadableEnum) -> Enum:
  t = [v for v in source_enum]
  values = [v.human_readable for v in source_enum]
  print(label)
  return t[cutie.select(values)]


def prompt_with_old_variants(label: str, old_variants: set[str]) -> str:
  if len(old_variants) == 0:
    return prompt(label)
  t = [v for v in old_variants]
  t.sort()
  t.insert(0, '>> Другое')
  print(label)
  selected = cutie.select(t)
  if selected == 0:
    value = prompt('Введите свой вариант')
    return value
  return t[selected]


def print_warning(text: str) -> None:
  print(f'\033[1;33m{text}\033[0m')


def print_error(text: str, label_length: int = 0) -> None:
  print('\033[A', end='')
  print(f'\033[{label_length - 2}C', end='')
  print(f' \033[31m({text})\033[0m: ', end='')


if __name__ == "__main__":
  main()

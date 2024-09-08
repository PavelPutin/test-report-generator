import click
import cutie
from enum import Enum
import os
import datetime
import pandas as pd
import configparser

class HumanReadableEnum(Enum):
  def __new__(cls, *args):
    value = len(cls.__members__) + 1
    obj = object.__new__(cls)
    obj._value_ = value
    return obj

  def __init__(self, human_readable = 'unknown'):
    self.human_readable = human_readable


class Priority(HumanReadableEnum):
  P_VALUE1 = 'Приоритет 1'
  P_VALUE2 = 'Приоритет 2'

  
class Severity(HumanReadableEnum):
  S_VALUE1 = 'Важность 1'
  S_VALUE2 = 'Важность 2'


class Status(HumanReadableEnum):
  BUG = 'Баг'
  INCIDENT = 'Инцидент'
  FEATURE = 'Фича'


class BugReport:
  id: int
  author: str
  creation_datetime: datetime.datetime
  brief: str
  expected: str
  actual: str
  reproduction_steps: list[str]
  status: Status
  priority: Priority
  seveirty: Severity

  def __str__(self):
    result = f"""{self.author}
{self.creation_datetime}
{self.brief}
{self.expected}
{self.actual}
"""
    for i, value in enumerate(self.reproduction_steps):
      result += f'{i + 1}. {value}\n'

    result += f"""{self.priority.human_readable}
{self.seveirty.human_readable}
{self.status.human_readable}"""
    return result


def main():
  config = init_from_ini()
  author = config['core']['author']
  xlsx = config['core']['xlsx']
  output_md = config['core']['output.md']

  df = init_from_xlsx(xlsx)
  while True:
    try:
      ids = df.get('ID')
      next_id = 1 if len(ids) == 0 else max(ids) + 1

      bug_report = prompt_bug_report(next_id, author)
      df.loc[len(df.index)] = [
        bug_report.id,
        bug_report.author,
        bug_report.creation_datetime,
        bug_report.priority.human_readable,
        bug_report.seveirty.human_readable,
        bug_report.status.human_readable,
        bug_report.brief,
        bug_report.expected,
        bug_report.actual,
        '\n'.join([f'{i}. {v}' for i, v in enumerate(bug_report.reproduction_steps)])
      ]
      output_md_filename = write_to_md_file(bug_report, output_md)
      print(f'Отчёт записан в \'{output_md_filename}\'')
    except KeyboardInterrupt:
      break
  write_to_xlsx_file(df, xlsx)


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
      'Краткое описание',
      'Ожидание',
      'Реальность',
      'Шаги воспроизведения',
    ])


def prompt_bug_report(next_id: int, author: str) -> BugReport:
  bug_report = BugReport()
  bug_report.id = next_id
  bug_report.author = author
  print(f'Отчёт о баге c id {bug_report.id}')
  bug_report.creation_datetime = datetime.datetime.now()
  bug_report.brief = prompt_brief()
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
    output.write('# Инцидент\n\n')
    output.write(f'**Приоритет:** {bug_report.priority.human_readable}\n\n')
    output.write(f'**Важность:** {bug_report.seveirty.human_readable}\n\n')
    output.write(f'**Статус:** {bug_report.status.human_readable}\n\n')
    output.write(f'**Время обнаружения**: {bug_report.creation_datetime}\n\n')
    output.write(f'**Автор:** {bug_report.author}\n\n')
    output.write(f'## Краткое описание\n\n')
    output.write(f'{bug_report.brief}\n\n')
    output.write(f'## Ожидание\n\n')
    output.write(f'{bug_report.expected}\n\n')
    output.write(f'## Реальность\n\n')
    output.write(f'{bug_report.actual}\n\n')
    output.write(f'## Шаги воспроизведения\n\n')
    if len(bug_report.reproduction_steps) != 0:
      for i, value in enumerate(bug_report.reproduction_steps):
        output.write(f'{i + 1}. {value}\n')
      output.write('\n')
    else:
      output.write(f'Шаги воспроизведения не указаны! Сообщите {bug_report.author}\n\n')
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


def print_warning(text: str) -> None:
  print(f'\033[1;33m{text}\033[0m')


def print_error(text: str, label_length: int = 0) -> None:
  print('\033[A', end='')
  print(f'\033[{label_length - 2}C', end='')
  print(f' \033[31m({text})\033[0m: ', end='')


if __name__ == "__main__":
  main()

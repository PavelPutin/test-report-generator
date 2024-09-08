import click
import cutie
from enum import Enum
import os
import datetime
import pandas as pd


class Priority(Enum):
  P_VALUE1 = 1
  P_VALUE2 = 2

  
class Severity(Enum):
  S_VALUE1 = 1
  S_VALUE2 = 2


class Status(Enum):
  BUG = 1
  INCIDENT = 2
  FEATURE = 3


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

    result += f"""{self.priority}
{self.seveirty}"""
    return result


def main():
  df, next_id = init_from_xlsx()

  bug_report = BugReport()
  bug_report.id = next_id
  bug_report.author = 'Pavel'
  bug_report.creation_datetime = datetime.datetime.now()
  bug_report.brief = prompt_brief()
  bug_report.expected = prompt('Ожидаемый результат:')
  bug_report.actual = prompt('Реальный результат:')
  bug_report.reproduction_steps = prompt_list('Шаги воспроизведения:')
  bug_report.priority = prompt_select('Приоритет:', Priority)
  bug_report.seveirty = prompt_select('Важность:', Severity)
  bug_report.status = prompt_select('Статус', Status)
  write_to_xlsx_file(bug_report, df, 'bugs.xlsx')


def init_from_xlsx() -> tuple[pd.DataFrame, int]:
  if os.path.exists('bugs.xlsx'):
    df = pd.read_excel('bugs.xlsx')
    ids = df.get('ID')
    next_id = 1 if len(ids) == 0 else max(ids) + 1
    return df, next_id
  else:
    return pd.DataFrame(columns=[
      'ID',
      'Автор',
      'Дата и время нахождения',
      'Приоритет',
      'Важность',
      'Краткое описание',
      'Ожидание',
      'Реальность',
      'Шаги воспроизведения',
    ]), 1


def write_to_md_file(bug_report: BugReport, filename: str) -> None:
  with open(filename, 'w') as output:
    output.write('# Инцидент\n\n')
    output.write(f'**Приоритет:** {bug_report.priority}\n\n')
    output.write(f'**Важность:** {bug_report.seveirty}\n\n')
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


def write_to_xlsx_file(bug_report: BugReport, df: pd.DataFrame, filename: str) -> None:
  df.loc[len(df.index)] = [
    bug_report.id,
    bug_report.author,
    bug_report.creation_datetime,
    bug_report.priority,
    bug_report.seveirty,
    bug_report.brief,
    bug_report.expected,
    bug_report.actual,
    '\n'.join([f'{i}. {v}' for i, v in enumerate(bug_report.reproduction_steps)])
  ]
  df.to_excel(filename, index=False)
  write_to_md_file(bug_report, f'BR_{bug_report.id}_{bug_report.priority}_{bug_report.seveirty}.md')


def prompt(label: str, required: bool = True) -> str:
  print(label, end=" ")
  value = input().strip()
  while required and value == '':
    print_error('Обязательное значение', len(label))
    value = input().strip()
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


def prompt_select(label: str, source_enum: Enum) -> str:
  values = [v.name for v in source_enum]
  print(label)
  return values[cutie.select(values)]


def print_warning(text: str) -> None:
  print(f'\033[1;33m{text}\033[0m')


def print_error(text: str, label_length: int = 0) -> None:
  print('\033[A', end='')
  print(f'\033[{label_length - 2}C', end='')
  print(f' \033[31m({text})\033[0m: ', end='')



if __name__ == "__main__":
  main()

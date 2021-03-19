# -*- coding: utf-8 -*-

from os import path
from typing import List
# Tabula also needs the java installed
import tabula
# Pandas dataframe type
from pandas import DataFrame
# Parse json to string
import json


def read_json(filepath: str) -> json:
    """
    Read a json file equivalent to student's grid.

    :Parameters:
        - `filepath`: path where to load the json file

    :Returns:
        - The equivalent json representation
    """
    out = NotImplemented
    with open(filepath) as f:
        out = json.loads(f.read())
    return out


def save_analysis(out: dict, filename: str, dirname: str) -> None:
    """
    Save the score into a json object

    Args:
        filename: the name of generated file
        dirname: place to put the output file

    Returns:
        Returns nothing
    """
    with open(path.join('..', dirname, filename + '.json'), 'w') as outfile:
        outfile.write(json.dumps(out))


def parse_pdf(studentId: str, inputDir: str, outDir: str = None) -> dict:
    """
    Read a student score and parse it to a json file

    Args:
      studentId: The student unique id
      inputDir: Directory where are placed the input files
      outDir: Where to save the json objects

    Returns:
      Returns nothing

    FIXME: Problem wiht columns in '2016015901' -:> SOLVED
    """

    # Read pdf file
    df = tabula.read_pdf(
        path.join(inputDir, f'historico_{studentId}.pdf'),
        pages='all'
    )

    # Internal function
    def get_before(dataframe: DataFrame, currentline: int, columname: str) -> str:
        """
        Search for lines above to get an non NaN value
        (Only work for string)

        Args:
            dataframe: Pandas dataframe containing
            currentline: The number that represetns the current line to search before
            columnname: Column's name to search for

        Returns:
            A string containing the usable value
        """
        i, value = currentline, ''
        while True:
            if i < 0:
                raise Exception(f'Ultrapassou o limite. Verifique o código.')
            value = dataframe.loc[i, columname]

            if type(value) is str:
                return value
            else:
                i -= 1

    # Internal function
    def fix_scores(dflist: List[DataFrame]) -> DataFrame:
        """
        Merge the multiples dataframes into a only one

        Args:
            dflist: A list of dataframes to search for

        Returns:
            A unique merged dataframe
        """
        scores = {}

        # ==
        def change_number(number: str) -> str:
            """
            Args:
                number: A value to convert the float format

            Returns:
                A new string that represents this value in '.' format
            """
            return number.replace(',', '.')

        # ==
        def change_key(val) -> str:
            """
            Check if type is string, if so, convert it and return (or just return)

            Args:
                val: a object that will be checked for its properties

            Returns:
                A new string
            """
            if (type(val) is str) and ('--' not in val):
                return float(change_number(val))
            else:
                return '--'

        # Itera sobre cada um dos dataframes de saída -> len == 7
        for table in dflist:
            # Pula se não for uma tabela de matérias concluídas/cursando
            if 'Ano/Período' not in table.columns.to_list():
                continue

            # Renaming columns
            cols = table.columns.to_list()
            fstRow = table.iloc[0]
            for i in range(len(cols)):
                if type(fstRow[i]) is str:
                    cols[i] = fstRow[i]
            table.columns = cols

            # print(f'Table names: {table.columns.to_list()}')

            # Itera sobre as matérias cursadas
            for turma in range(0, table.shape[0]):

                # Fix the case when there's another column
                if 'Unnamed: 1' in table.columns:
                    sigla = table.loc[turma, 'Unnamed: 1']
                else:
                    sigla = table.iloc[turma, 1]

                # Pula se o valor da coluna não for a sigla da matéria
                if type(sigla) is not str or len(sigla) < 3:
                    continue
                # Resolve o problema caso não apareça os elementos corretos
                periodo = get_before(table, turma, 'Ano/Período')
                freq = change_key(table.loc[turma, 'Freq %'])
                nota = change_key(table.loc[turma, 'Média'])
                sit = table.loc[turma, 'Situação']
                if type(sit) is not str:
                    sit = '--'

                # Caso contrário, adiciona no scores
                if periodo not in scores:
                    scores[periodo] = {}
                scores[periodo][sigla] = {
                    'scores': nota,
                    'situation': sit,
                    'freq': freq
                }

        # Return the output dict
        return scores

    # Run the file scrapping
    out = fix_scores(df)

    # Save to file
    if outDir is not None:
        save_analysis(out, studentId, outDir)

    # Return the json object
    return out

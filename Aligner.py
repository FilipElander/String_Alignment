
from __future__ import print_function
import argparse
import codecs
import numpy as np
import json
import requests


"""
This module computes the minimum-cost alignment of two strings (minimal edit)
"""


"""
When printing the results, only print BREAKOFF characters per line.
"""
BREAKOFF = 60


def compute_backpointers(s0, s1):  #Tillverkar en array med backpointrs
    """
    <p>Computes and returns the backpointer array (see Jurafsky and Martin, Fig 3.27)
    arising from the calculation of the minimal edit distance of two strings
    <code>s0</code> and <code>s1</code>.</p>

    <p>The backpointer array has three dimensions. The first two are the row and
        column indices of the table in Fig 3.27. The third dimension either has
    the value 0 (in which case the value is the row index of the cell the backpointer
    is pointing to), or the value 1 (the value is the column index). For example, if
    the backpointer from cell (5,5) is to cell (5,4), then
    <code>backptr[ =5</code> and <code>backptr[5][5][1]=4</code>.</p>

    :param s0: The first string.
    :param s1: The second string.
    :return: The backpointer array.
    """
    if s0 == None or s1 == None:
        raise Exception('Both s0 and s1 have to be set')
    rows = len(s0)+1        # antalet rader
    columns = len(s1)+1     # antalet kolumner

    ####### Tillverkar  Levenshtein matrisen ########
    # Gör en tom matris med nollor
    distance = [[0 for y in range(len(s1)+1)] for x in range(len(s0)+1)]

    # Gör de yttre lagrerna i matrisen 0 -> len(str) vertikalt och horisontellt
    for i in range(1,rows):
        distance[i][0] = i
    for i in range(1,columns):
        distance[0][i] = i

    # Beräknar kostnaderna för varje plats inne i matrisen och sätter in dem
    # kollar om bokstaven på indexet i de två orden är samma i sådana fall kostar det 0
    # och skall ha samma värde som diagonalt innan, annars kostar det 1 från över eller underself.
    for column in range(1,columns):
        for row in range(1,rows):   # kolla varje rad i vare column
            if s0[row-1] == s1[column -1]: # om det är samma bokstav kostar det 0
                c = 0
            else: # annars kostar det 2
                c = 2
            distance[row][column] = min(distance[row-1][column] + 1,distance[row][column-1] + 1,distance[row-1][column-1] + c)
            # raden över säger att det minsta värdet av över eller bredvid + 1 eller diagonalt innan plus (0 eller 2)
            # skall sättas in på platsen i matrisen.

    # det minsta avståndet är
    cost = distance[row][column]
    print("totalkostnaden är")
    print(cost)


    ####### Tillverkar  backptr-matrisen ########
    # Tillverkar en tom matris med [0,0] för till backptr-matrisen
    backptr = [[[0, 0] for y in range(len(s1)+1)] for x in range(len(s0)+1)]

    # går igenom platserna i Levenshtein matrisen bakirfrån
    for column in range(columns-1,0,-1):
        for row in range(rows-1,0,-1):
            # Om värdet till vänster är det minsta: peka vänster
            if distance[row][column-1] == min(distance[row-1][column-1],distance[row][column-1],distance[row-1][column]):
                backptr[row][column][0] = row
                backptr[row][column][1] = column -1
            # Om värdet över är det minsta: peka upp
            if distance[row-1][column] == min(distance[row-1][column-1],distance[row][column-1],distance[row-1][column]):
                backptr[row][column][0] = row -1
                backptr[row][column][1] = column
            # om värdet diagonalt är minst: peka på diagonalt
            if distance[row-1][column-1] == min(distance[row-1][column-1],distance[row][column-1],distance[row-1][column]):
                backptr[row][column][0] = row-1
                backptr[row][column][1] = column -1

    # Gör yttervärdena i matrisen, (OBS behövs ej)
    for i in range(0,rows):
        j = i-1
        backptr[i][0][0] = j
        backptr[i][0][1] = 0
    for i in range(0,columns):
        j = i-1
        backptr[0][i][1] = j
        backptr[0][i][0] = 0

    return backptr


def subst_cost(c0, c1): # Beräknar kostnaden efter att det blivit länkat
    """
    The cost of a substitution is 2 if the characters are different
    or 0 otherwise (when, in fact, there is no substitution).
    """
    return 0 if c0 == c1 else 2         # Om charachter 0 är samma som charachter 1 kostar det 0 annars 2.



def align(s0, s1, backptr): # Lägger de rätt för att få bästa matching med letters
    """
    <p>Finds the best alignment of two different strings <code>s0</code>
    and <code>s1</code>, given an array of backpointers.</p>

    <p>The alignment is made by padding the input strings with spaces. If, for
    instance, the strings are <code>around</code> and <code>rounded</code>,
    then the padded strings should be <code>around  </code> and
    <code> rounded</code>.</p>

    :param s0: The first string.
    :param s1: The second string.
    :param backptr: A three-dimensional matrix of backpointers, as returned by
    the <code>diff</code> method above.
    :return: An array containing exactly two strings. The first string (index 0
    in the array) contains the string <code>s0</code> padded with spaces
    as described above, the second string (index 1 in the array) contains
    the string <code>s1</code> padded with spaces.
    """

    # Tom array att fylla på och returnera
    result = ['','']
    # Gör strängarna till lätthanterligare arrays
    x0 = [char for char in s0]
    x1 = [char for char in s1]
    # toma arrays att stoppa in de alignade bokstäverna och spacen
    ress0 = []
    ress1 = []

    rows = len(s0)
    columns = len(s1)

    # Tillverkar botten värden i backptr-matrisen så att man skall veta när man är klar
    backptr[0][0][0] = -1
    backptr[0][0][1] = -1

    # initiering värden vart i backptr-matrisen man är och har kommit ifrån
    staterow = rows
    statecol = columns
    r = staterow
    c = statecol
    # den går går längst pekarna tills den når botten
    while staterow >=0  and statecol >=0:
        # Om den pekar diagonalt
        if backptr[staterow][statecol][0] == staterow-1 and backptr[staterow][statecol][1] == statecol-1 :
            if staterow == 0 and statecol == 0: # om den är i botten, passera
                pass
            else:
                # annars spara båda bokstäverna på sammam plats i result
                ress0.insert(0,x0[staterow-1])
                ress1.insert(0,x1[statecol-1])
        # Om den pekar vänster (samma row)
        if backptr[staterow][statecol][0] == staterow:
            if staterow == 0 and statecol == 0: # om den är i botten, passera
                pass
            else:
                # annars spacear den raden och stoppar in bokstaven i kolumnen
                ress0.insert(0," ")
                ress1.insert(0,x1[statecol-1])
        # Om den pekar upp (samma kolumn)
        if backptr[staterow][statecol][1] == statecol:
            if staterow == 0 and statecol == 0: # om den är i botten, passera
                pass
            else:
                # annars spacear den kolumnen och stoppar in bokstaven i raden
                ress0.insert(0,x0[staterow-1])
                ress1.insert(0," ")

        # för att inte skriva över staterow i ny initieringen
        r = staterow
        c = statecol
        # initierar de nya tillståndet (följer pekaren)
        staterow = backptr[r][c][0]
        statecol = backptr[r][c][1]

    # printfunktionen vill ha stringen bakvänd....
    ress0.reverse()
    ress1.reverse()
    # concattar arrayerna till en sträng igen
    sum0 =''.join(ress0)
    sum1 =''.join(ress1)
    # stoppar in i resultatet
    result[0]=sum0
    result[1]=sum1

    return(result)

def print_alignment(s):
    """
    <p>Prints two aligned strings (= strings padded with spaces).
    Note that this printing method assumes that the padded strings
    are in the reverse order, compared to the original strings
    (because we are following backpointers from the end of the
    original strings).</p>

    :param s: An array of two equally long strings, representing
    the alignment of the two original strings.
    """
    if s[0] == None or s[1] == None:
        return None
    start_index = len(s[0]) - 1
    while start_index > 0:
        end_index = max(0, start_index - BREAKOFF + 1) # om ordet är längre än 60 char blir det större än noll och slutar där (för extremt långa ord )
        print_list = ['', '', ''] # Gör en array med char som insert
        for i in range(start_index, end_index-1 , -1):  #range(start,stop,step) => (längden,0,-1)
            print_list[0] += s[0][i]                            #skriver bokstäverna från string0
            print_list[1] += '|' if s[0][i] == s[1][i] else ' ' # om det är samma så skriver den "|" i mellersta arrayen annars tomt
            print_list[2] += s[1][i]                            # skriver bokstav från array[1]

        for x in print_list: print(x)                           # Printar varje array
        start_index -= BREAKOFF

def main():
    """
    Parse command line arguments
    """
    ## In argument hanterare
    parser = argparse.ArgumentParser(description='Aligner')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', '-f', type=str, nargs=2, help='align two strings')
    group.add_argument('--string', '-s', type=str, nargs=2, help='align the contents of two files')

    parser.add_argument('--check', action='store_true', help='check if your alignment is correct')

    arguments = parser.parse_args() # In argumenten skrivna i temrinalen


### Behandlar in argumenetn och gör det till två strängar s0[] & s1[]
## Eller om det är en url som skall checka om man gjort rätt.
    if arguments.file:
        f1, f2 = arguments.file
        with codecs.open(f1, 'r', 'utf-8') as f:
            s1 = f.read().replace('\n', '')
        with codecs.open(f2, 'r', 'utf-8') as f:
            s2 = f.read().replace('\n', '')

    elif arguments.string:
        s1, s2 = arguments.string

    if arguments.check:
        payload = json.dumps({
            's1': s1,
            's2': s2,
            'result': align(s1, s2, compute_backpointers(s1, s2))
        })
        response = requests.post(
            'https://language-engineering.herokuapp.com/correct',
            data=payload,
            headers={'content-type': 'application/json'}
        )
        response_data = response.json()
        if response_data['correct']:
            print_alignment( align(s1, s2, compute_backpointers(s1, s2)))
            print('Success! Your results are correct')
        else:
            print('Your results:\n')
            print_alignment( align(s1, s2, compute_backpointers(s1, s2)))
            print("The server's results\n")
            print_alignment(response_data['result'])
            print("Your results differ from the server's results")
    else:
        print_alignment( align(s1, s2, compute_backpointers(s1, s2)))


if __name__ == "__main__":
    main()

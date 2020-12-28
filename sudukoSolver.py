import numpy as np
import sys
from itertools import combinations

#=============================================================================================================================================
#
#   Mark Smith
#   -----------
#
#   V1.0 - 28-Dec-2020  - Initial Version
#
#   Terminology:
#       - Grid - This is the main 9x9 suduko grid
#       - Cell - The individual elements inside the grid. There are 9x9 of these.
#       - Row - 9 rows across the grid (each with 9 cells)
#       - Column - 9 columns down the grid (each with 9 elements)
#       - mini-grid - 3x3 sub-grids which divide the main grid into 9
#       - mini-row - the 3 rows inside a mini-grid (3 elements)
#       - mini-col - the 3 columns inside a mini-grid (3 elements)
#       - Block - a distinct set of cells. Could refer to the main grid, a row, a column, a mini-grid, etc.
#       - Candidate - Each cell has a number of candidate values (initially these are 1-9). The objective is to get this to just one.
#       - Value - When a cell is solved, its value is set
#       - Dependant - Each cell is has a number of dependants. Setting the value on a cell will update its dependant.  
#
#       A description of the suduko techniques employed can be found here:  https://www.youtube.com/watch?v=b123EURtu3I 
#   
#   High Level Code Flow:
#       - Create an initial full grid (no values set and all candidates possible)
#       - Apply the initial set of values from file.
#       - The following suduko techniques are then applied against the grid: Hidden Pairs, X Wing, Naked Triples, Naked Quads, Claim Pair/Triple, 
#         Pointing Pair/Triple, Naked Pairs, Hidden Singles, Naked Singles. Whenever a cell is solved, i.e. value set, then its dependants are 
#         are updated. 
#       - This is repeated until all values have been found, i.e. grid is solved, or it's not possible to solve any further cells. 
#       - If the grid has not been solved then a brute force attack is attempted. This involves identifying cells with only two candidates and trying 
#         each of these for each cell, following the logic above. 
#       - If the brute force attack fails then we admit defeat and display the list of remaining candidates for each cell.
#         Note: The solution has not failed yet...
#==============================================================================================================================================

#============================================
# Functions / Procedures
#============================================

def createGrid():
    # Each Cell is represented with a 3 value tuple. (value, list of candidates, list of dependants)
    
    # Create Initial grid 
    gridOut = [(0, [1,2,3,4,5,6,7,8,9], getMyDependants(x)) for x in range(CELLS)]
    
    # Load initial values from file.
    for v in loadValuesFromFile():
        # Prime each cell given an initial value for update, i.e. make it a naked single. 
        gridOut[v[0]] = (0, [v[1]], gridOut[v[0]][2])
    
    # Now apply these initial values.
    doNakedSingle(gridOut)
    return gridOut 

def loadValuesFromFile():
    
    # Reads input from file and returns as a list of values for each cell index.
    with open("grid.txt") as f:
        content = f.read().replace('\n', '')
    f.close()

    values = []
    for i, c in enumerate(content):
        if c != '-':
            values.append((i, int(c)))

    return values

def drawGrid(gridIn):
    vals = [x[0] for x in gridIn]
    print(np.array(vals).reshape((9,9))) 

def numOutstandingCells(gridIn):
    return len([x for x in gridIn if x[0] == 0])

def numOutstandingCandidates(gridIn):
    count = 0
    for i in gridIn:
        count = count + len(i[1])
    return count

def getCellIndex(rowIn, colIn):
    return (rowIn * 9) + colIn

def getRowCells(rowRefIn):
    return [x for x in range(rowRefIn * 9, (rowRefIn * 9) + 9)]

def getColCells(colRefIn):
    return [x for x in range(colRefIn, (colRefIn + 73), 9)]

def getRow(myCellRef):
    return int(myCellRef / 9)

def getCol(myCellRef):
    return int(myCellRef % 9)

def getMiniGridCells(mbRefIn):
    return  MINI_GRID_CELLS[mbRefIn]   

def getMyRowPals(myCellRef):
    myRow = getRow(myCellRef)
    return [x for x in getRowCells(myRow) if x != myCellRef]
    
def getMyColPals(myCellRef):
    myCol = getCol(myCellRef)
    return [x for x in getColCells(myCol) if x != myCellRef]

def getMyMiniGridPals(myCellRef):
    myMiniGrid = getMyMiniGrid(myCellRef)
    return [x for x in MINI_GRID_CELLS[myMiniGrid] if x != myCellRef]

def getMyMiniGrid(myCellRef):
    myRow = getRow(myCellRef)
    myCol = getCol(myCellRef)

    if myRow in [0,1,2]:
        a = {0,1,2}
    elif myRow in [3,4,5]:
        a = {3,4,5}
    elif myRow in [6,7,8]:
        a = {6,7,8}
    else:
        raise Exception("getMyMiniGrid Error") 

    if myCol in [0,1,2]:
        b = {0,3,6}
    elif myCol in [3,4,5]:
        b = {1,4,7}
    elif myCol in [6,7,8]:
        b = {2,5,8}
    else:
        raise Exception("getMyMiniGrid Error")

    return list(a.intersection(b))[0]

def getMyMiniGridPals(myCellRef):
    myMiniGrid = getMyMiniGrid(myCellRef)
    return [x for x in MINI_GRID_CELLS[myMiniGrid] if x != myCellRef]

def getMyDependants(myCellRef):
    return list(set(getMyColPals(myCellRef) + getMyRowPals(myCellRef) + getMyMiniGridPals(myCellRef)))

def getBlockValues(gridIn,blockIn):
    return [gridIn[x][0] for x in blockIn if gridIn[x][0] != 0 ]

def getBlockCandidatesByCell(gridIn, blockIn):
    # This returns a list of possibles for each cell (list of lists)
    return [gridIn[x][1] for x in blockIn]
    
def getBlockCandidates(gridIn, blockIn):
    # This returns just a flat list of distinct possibles for the block
    return list(set([item for sublist in getBlockCandidatesByCell(gridIn, blockIn) for item in sublist])) 

def onlyTwoElements(listIn):
    if len(listIn) == 2:
        return listIn
    return []    

def getMiniGridRowRefs(miniBlockIn):
    rowRefs = []
    for i in range(3):
        rowRefs.append([miniBlockIn[j] for j in range(i*3, (i*3) + 3)])
    return rowRefs

def getMiniGridColRefs(miniBlockIn):
    colRefs = []
    for i in range(3):
        colRefs.append([miniBlockIn[j] for j in range(i, i+7, 3)])
    return colRefs

def getCandidateIsPossibilityCount(gridIn, blockIn, valIn):
    return len([p for p in blockIn if valIn in gridIn[p][1]])

def removeCandidateFromCells(gridIn, cellsIn, candidateIn):
    for cell in cellsIn:
         gridIn[cell] = (gridIn[cell][0], [a for a in gridIn[cell][1] if a != candidateIn] ,gridIn[cell][2] )


def checkMiniRowColForPPoT(gridIn, miniBlockIn, typeIn):
    
    count = 0

    # Get the list of miniLines, dependant on type (row or col)
    if typeIn == 'R':
        miniLines = getMiniGridRowRefs(miniBlockIn)
    else:
        miniLines = getMiniGridColRefs(miniBlockIn)

    # Let's check each mini-Line
    for miniLine in miniLines:
        # Check each candidate against each mini-row 
        
        for c in range(1,10):
            # Check for 2 or more adjacent cells with c as a possible value.
            # First check middle line, as we can only have adjacent cells if it's a possibility here 
            if c in gridIn[miniLine[1]][1]:
                # We have a pointing pair/triple if:
                #   -  candidate is a possibility in two or more cells AND
                #   -  candidate is not a possibility elsewhere in this mini-grid
                miniLineCount = getCandidateIsPossibilityCount(gridIn, miniLine, c)

                if miniLineCount >= 2 and miniLineCount == getCandidateIsPossibilityCount(gridIn, miniBlockIn, c):             
                    # OK, we do have one. So we need to remove this candidate from cells in same row (outside of this mini-block)
                    if typeIn == 'R':
                        fullLine = getRowCells(getRow(miniLine[0]))
                    else: 
                        fullLine = getColCells(getCol(miniLine[0]))                   

                    cellsToUpdate = [t for t in fullLine if t not in miniLine]
                    removeCandidateFromCells(gridIn, cellsToUpdate, c)

def solveCell(gridIn, indexIn):
     # Cell is solved. So, set it's value, empty its possibility list and inform its dependants.
    newVal = gridIn[indexIn][1][0]
    gridIn[indexIn] = (newVal, [], gridIn[indexIn][2])
    
    # We now need to inform its dependants, so they can remove the value from their list of possible values.
    for dependant in gridIn[indexIn][2]:
        # Simply remove the value just set from the dependant (as it can't be this value)
        gridIn[dependant] = (gridIn[dependant][0], [x for x in gridIn[dependant][1] if x != newVal], gridIn[dependant][2] )

def doNakedSingle(gridIn):
    updateCount = 0
    #  Loop through the grid processing naked singles, i.e. cells with only one possibility left
    for i, cell in enumerate(gridIn):
        if (len(cell[1]) == 1 and cell[0] == 0):
            solveCell(gridIn, i)        
            updateCount = updateCount +  1
    return updateCount

def doHiddenSingles(gridIn):
    # A cell with multiple candidates is called a Hidden Single if one of the candidates is the only candidate in a row, a column
    # or a mini-grid. The single candidate is the solution to the cell. All other appearances of the same candidate, if any, are elimiated 
    # if they can be seen by the single. 

    preCount = numOutstandingCandidates(gridIn)
    lineFunctions = [getRowCells, getColCells, getMiniGridCells]

     # Work through rows, columns and mini-grids in turn
    for f in lineFunctions:
        for a in range(9):
            block = f(a)
            blockPossibles = getBlockCandidates(gridIn, block)

            for i in blockPossibles:       
                count = 0
                for j in block:
                    if i in gridIn[j][1]:
                        hiddenSingle = j
                        count = count + 1
                        if count > 1:
                            break
                # If just once instance of the value then we have a hidden single. Let's set it possible value, which will lead 
                # to the cell being solved as a naked single.
                if count == 1: gridIn[hiddenSingle] = (0, [i], gridIn[hiddenSingle][2])
                    
    postCount = numOutstandingCandidates(gridIn)
    return preCount - postCount


def doPPoT(gridIn):

    # Identify Pointing Pairs or Triples..
    preCount = numOutstandingCandidates(gridIn)

    # Work through each mini-grid in turn
    for i in range(9):
        miniGrid = getMiniGridCells(i)
        checkMiniRowColForPPoT(gridIn, miniGrid, 'R')
        checkMiniRowColForPPoT(gridIn, miniGrid, 'C')

    postCount = numOutstandingCandidates(gridIn)

    return preCount - postCount

def doClaimingPoT(gridIn):
    # Identify and process Claiming Pairs or Triples
    # When a certain candidate appears in only 2 (or 3) cells in a row of col, and the cells are also in a mini-grid, they are called
    # a claiming pair (or triple).
    # All other appearances of the candidate in the same mini-grid, if any, can be eliminated. 

    preCount = numOutstandingCandidates(gridIn)
    lineFunctions = [getRowCells, getColCells, getMiniGridCells]

    # Work through rows then columns in turn  (called line below)
    for f in lineFunctions:
        for i in range(9):
            line = f(i)
            # Check how many times each candidate is still a possibility in this line. If 2 or 3 then a possible claiming pair (or triple)
            for c in range(1,10):
                cCount = getCandidateIsPossibilityCount(gridIn, line, c)
                if cCount == 2 or cCount == 3:
                    # Now check each mini row or col inside this row or col. If a match then we do have a claiming pair (or triple)
                    for x in range(0, 7, 3):
                        miniLine = [line[x], line[x+1], line[x+2]]
                        mcCount = getCandidateIsPossibilityCount(gridIn, miniLine, c)
                        if cCount == mcCount:
                            miniGrid = getMiniGridCells(getMyMiniGrid(miniLine[0]))
                            cellsToUpdate = [t for t in miniGrid if t not in miniLine]
                            removeCandidateFromCells(gridIn, cellsToUpdate, c)
                            break
                        else:
                            if mcCount > 0: break

    postCount = numOutstandingCandidates(gridIn)
    return preCount - postCount


def doNakedPairs(gridIn):

    preCount = numOutstandingCandidates(gridIn)

    blockFunctions = [getRowCells, getColCells, getMiniGridCells]

    # Loop through all the rows, columns and then mini-grids
    for f in blockFunctions:
        for i in range(9):
            # Loop through every instance of the block (i.e. row, col, or 3x3 grid)
            block = f(i)
            possiblesByCell = getBlockCandidatesByCell(gridIn, block)
            twoAndNullElementPossibles = [onlyTwoElements(x) for x in possiblesByCell]
            twoElementPossibles = [x for x in twoAndNullElementPossibles if x != []]
            nakedPairs = [x for x in twoElementPossibles if twoElementPossibles.count(x) == 2]
            candidatesToRemove = list(set([item for sublist in nakedPairs for item in sublist])) 

            cellsToUpdate = [x for x in block if gridIn[x][1] not in nakedPairs and gridIn[x][0] == 0]
            [removeCandidateFromCells(gridIn, cellsToUpdate, c) for c in candidatesToRemove ]

    postCount = numOutstandingCandidates(gridIn)

    return preCount - postCount



def doNakedTriplesQuads(gridIn):
     # Three cells in a row, column or mini-grid, having only the same three candidates, or their subset, are called a naked triple.
     # All other appearances of the same candidates can be eliminated, if they are in the same row, column or mini-grid.
     #
     # Four cells in a row, column or mini-grid, having only the same four candidates, or their subset, are called a naked quad.
     # All other appearances of the same candidates can be eliminated, if they are in the same row, column or mini-grid.

    preCount = numOutstandingCandidates(gridIn)

    # Set up types list; 3 represents Triple and 4 Quad
    types = [3,4]

    blockFunctions = [getRowCells, getColCells, getMiniGridCells]

    checkingSet = set()

    # Look for Triples first and then Quads. 

    for t in types:

        # Loop through all the rows, columns and then mini-grids
        for f in blockFunctions:
            for i in range(9):
                block = f(i)

                # We're only interested in cells that have 2 to 3 candidates for Triples, or 2 to 4 for Quads          
                possibles = [cell for cell in block if len(gridIn[cell][1]) > 1 or len(gridIn[cell][1]) <= t]
                
                if len(possibles) < t: continue
            
                # If there are more than 3 (or 4) such cells, then we'll need to check the 3 (or 4) cell combinations of these. 
                combs = list(combinations(possibles, t)) 
                for comb in combs:
                    # Add the candidates for the combination to a set. A pointing triple will have 3 possibilities.
                    checkingSet.clear()
                    # Double check each cell in this combination has more than one combination, as these could re reduced from a previous combination
                    if t == 3:
                        if len(gridIn[comb[0]][1]) <= 1 or len(gridIn[comb[1]][1]) <= 1 or len(gridIn[comb[2]][1]) <= 1:
                            continue
                    else:
                        if len(gridIn[comb[0]][1]) <= 1 or len(gridIn[comb[1]][1]) <= 1 or len(gridIn[comb[2]][1]) <= 1 or len(gridIn[comb[3]][1]) <= 1:
                            continue
    
                    for j in range(t):
                        [checkingSet.add(val) for val in gridIn[comb[j]][1]]
                        if len(checkingSet) > t: 
                            break                 
                    if len(checkingSet) == t:
                        # We have a pointing triple or Quad. Let's remove these as canidates from other cells in row, col or mini-grid.
                        if t == 3:
                            cellsToUpdate = [e for e in block if e != comb[0] and e != comb[1] and e != comb[2]]
                        else:
                             cellsToUpdate = [e for e in block if e != comb[0] and e != comb[1] and e != comb[2] and e != comb[3]]
                        [removeCandidateFromCells(gridIn, cellsToUpdate, c) for c in checkingSet ]

    postCount = numOutstandingCandidates(gridIn)
    return preCount - postCount

def doXWing(gridIn):

    # When a candidate appears in four cells that form the corners of a rectangle (or square) 
    # and it appears only in the two cells in both rows, all other appearances of the candidate 
    # in the two columns, if any, can be elimated. It also works if the rows and columns are switched.

    preCount = numOutstandingCandidates(gridIn)
    blockFunctions = [getRowCells, getColCells]
    oppFunctions = [getColCells, getRowCells]

    # First try rows (elimating from crossing columns).
    # They try columns (eliminating from crossing rows)

    for e, bf in enumerate(blockFunctions):
        xwPossibles = []
        xwDefinites = []
        
        # Identify xwing possibles.... (look for candidates that only exist in 2 cells of this line) 
        for i in range(9):
            line = bf(i)          
            candidatesByCell = getBlockCandidatesByCell(gridIn, line)
            flatCandidatesByCell = [item for sublist in candidatesByCell for item in sublist]
            xwPossibleValues = list(set([i for i in flatCandidatesByCell if flatCandidatesByCell.count(i) == 2]))
            
            for p in xwPossibleValues:
                indexes = [index for index,choices in enumerate(candidatesByCell) if p in choices ]
                xwPossibles.append((p, i, indexes[0], indexes[1]))

        # We have some possibles. Let's cross check to see if a second line makes the rectangle (or square). 
        for m, xwp in enumerate(xwPossibles):
            for n in range(m+1, len(xwPossibles)):
                if xwp[0] == xwPossibles[n][0] and xwp[2] == xwPossibles[n][2] and xwp[3] == xwPossibles[n][3]:
                    xwDefinites.append(xwp)
                    xwDefinites.append(xwPossibles[n])
       
        # We now have some xwings, lets handle them...
        for s in range(0, len(xwDefinites), 2):
            # If we are looking at rows, then we want the crossing column, and vice versa.
            oppositeA = oppFunctions[e](xwDefinites[s][2])
            oppositeB = oppFunctions[e](xwDefinites[s][3])            
            toUpdateA = [h for g,h in enumerate(oppositeA) if g != xwDefinites[s][1] and  g != xwDefinites[s+1][1]]
            toUpdateB = [h for g,h in enumerate(oppositeB) if g != xwDefinites[s][1] and  g != xwDefinites[s+1][1]]
            removeCandidateFromCells(gridIn, toUpdateA, xwDefinites[s][0])
            removeCandidateFromCells(gridIn, toUpdateB, xwDefinites[s][0])
            
    postCount = numOutstandingCandidates(gridIn)
    #print(f"X Wing - Before = {preCount}  Post = {postCount}")
    return preCount - postCount

def doHiddenPairs(gridIn):
    # When a pair of candidates appear in only two cells in a row, col or mini-grid, but aren't the only candidates in the cells, 
    # they are called a hidden pair. All candidates other than the pair in the cells can be eliminated, yielding a naked pair.

    preCount = numOutstandingCandidates(gridIn)
    blockFunctions = [getRowCells, getColCells, getMiniGridCells]

    # Loop through all the rows, columns and then mini-grids
    for f in blockFunctions:
        for i in range(9):
            # Loop through every instance of the block (i.e. row, col, or 3x3 grid)
            block = f(i)
            candidatesByCell = getBlockCandidatesByCell(gridIn, block)
            flatCandidatesByCell = [item for sublist in candidatesByCell for item in sublist]
            hpPossValues = list(set([i for i in flatCandidatesByCell if flatCandidatesByCell.count(i) == 2]))
            if len(hpPossValues) > 1:
                hpPossCombos = list(combinations(hpPossValues, 2))
                for c in hpPossCombos:
                    possibleCells = [a for a in candidatesByCell if len(a) > 2 and c[0] in a and c[1] in a]
                    if len(possibleCells) == 2:
                        indexes = [index for index,cell in enumerate(candidatesByCell) if cell in possibleCells ]
                        cellsToUpdate = [block[a] for a in indexes]
                        candidatesToRemove = [x for x in range(1, 10) if x != c[0] and x != c[1]]
                        [removeCandidateFromCells(gridIn, cellsToUpdate, z) for z in candidatesToRemove]
                        
    postCount = numOutstandingCandidates(gridIn)
    #print(f"HiddenPairs - Before = {preCount}  Post = {postCount}")
    return preCount - postCount


def updateGrid(gridIn):
    return doHiddenPairs(gridIn) + doXWing(gridIn) + doNakedTriplesQuads(gridIn) +  doClaimingPoT(gridIn) + doPPoT(gridIn) + doNakedPairs(gridIn) + doHiddenSingles(gridIn) + doNakedSingle(gridIn)
    
def tryBruteForce(gridIn):

    print(f"\nOK, we couldn't solve using the provided techniques... Let try brute force")

    # Get list of cells with two candidates and try these
    twoCandidateCells = [i for i, x in enumerate(gridIn) if len(x[1]) == 2]

    for cell in twoCandidateCells:
        # Try setting each of the two values, and see if it solves the grid...
        for candidate in gridIn[cell][1]:
            copyGrid = gridIn.copy()
            copyGrid[cell] = (0, [candidate], copyGrid[cell][2])
            solveCell(copyGrid, cell)
            iteration = 1
            while (updateGrid(copyGrid) and numOutstandingCells(copyGrid) > 0 ):
                iteration = iteration + 1
            if numOutstandingCells(copyGrid) == 0: 
                return copyGrid
    return 0

#============================================
# Globals / Constants
#============================================

CELLS = 9 * 9
MINI_GRID_CELLS = [ [0,1,2,9,10,11,18,19,20], 
                    [3,4,5,12,13,14,21,22,23],
                    [6,7,8,15,16,17,24,25,26],
                    [27,28,29,36,37,38,45,46,47],
                    [30,31,32,39,40,41,48,49,50],
                    [33,34,35,42,43,44,51,52,53],
                    [54,55,56,63,64,65,72,73,74],
                    [57,58,59,66,67,68,75,76,77],
                    [60,61,62,69,70,71,78,79,80]
                     ]

#============================================
# Main Program
#============================================

try:
     
    sudukoGrid = createGrid()    
    drawGrid(sudukoGrid)

    input("Press Enter to solve......")

    iteration = 1
    while (updateGrid(sudukoGrid) and numOutstandingCells(sudukoGrid) > 0 ):
        print(f"After Iteration {iteration} - Outstanding Cells = {numOutstandingCells(sudukoGrid)} outstanding candidates = {numOutstandingCandidates(sudukoGrid)}")
        iteration = iteration + 1

    print(f"Complete - Outstanding Cells = {numOutstandingCells(sudukoGrid)} outstanding candidates = {numOutstandingCandidates(sudukoGrid)}")
    drawGrid(sudukoGrid)

    if numOutstandingCells(sudukoGrid) > 0:
        # We couldn't solve the grid using the techniques provided. As a last resort try brute force on cells with two candidates
        bruteForceGrid = tryBruteForce(sudukoGrid)
        if not bruteForceGrid:
            print(f"Brute Force Failed!!!..... Outstanding Candidates")
            for i in range(9):
                print(f" {getBlockCandidatesByCell(sudukoGrid, getRowCells(i))}")
        else:
            print(f"Brute Force Success ")
            drawGrid(bruteForceGrid)
       
except Exception as e:
    print("Aborting..../n", e)
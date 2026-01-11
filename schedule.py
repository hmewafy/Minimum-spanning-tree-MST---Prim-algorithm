import random
from typing import List, Dict, Optional, Tuple
import itertools
import heapq

Match = Tuple[int, int]  # e.g. (teamA_ID, teamB_ID)

class Stadium:
    """
    A stadium can host exactly one match per day.
    """
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name

    def __repr__(self) -> str:
        return f"Stadium({self.id}, {self.name})"

DaySchedule = Dict[str, Match] 
Schedule = List[DaySchedule]

# ---------------------------------------------------------
# Generate all permutations of length k
# -----------------------------------------------  ------------
def k_permutations(arr: List, k: int) -> List[List]:
    """
    Returns all permutations of 'arr' taken k at a time.
    """
    return list(itertools.permutations(arr, k))

# ------------------------------------------------------------
# Generate single-day assignments for a block of matches
# ------------------------------------------------------------
def generate_assignments(block: List[Match], stadiums: List[Stadium]) -> List[DaySchedule]:
    """
    Produce all feasible ways to assign each match in 'block' to a distinct stadium,
    provided len(block) <= len(stadiums).

    If more matches than stadiums, we return [] indicating no valid assignment.
    Each returned DaySchedule is a dict: {stadium_id: match, ...}
    """
    if len(block) > len(stadiums):
        return []

    assignments: List[DaySchedule] = []
    # We create permutations of length len(block).
    # This ensures each match is assigned to a unique stadium.
    perms = k_permutations(stadiums, len(block))
    for perm in perms:
        day_sched: DaySchedule = {}
        for i, match in enumerate(block):
            day_sched[perm[i].id] = match
        assignments.append(day_sched)

    return assignments

# ---------------------------------------------   --------------
# get_optimizing_solution: DP subroutine
# ----------------------------------------------------
def get_optimizing_solution(
    i: int,
    dp: List[Optional[Schedule]],
    matches: List[Match],
    stadiums: List[Stadium]
) -> Optional[Schedule]:
    """
    Computes a minimal day-schedule from match i..end, or None if infeasible.

    INVARIANT OUTCOMES:
      Oa: dp[j] for j>i is minimal or None.
      Ob: We only combine a single-day assignment if dp[i+k] is not None.
      Oc: dp[i] is updated to the best (fewest total days) or remains None.

    Corner Cases:
    - If no day assignment merges with dp[i+k], dp[i] = None.
    - If a block (i..i+k) is bigger than stadiums, no assignment is generated.
    """
    n = len(matches)
    m = len(stadiums)
    best: Optional[Schedule] = None

    # We can schedule up to m matches in a single day
    for k in range(1, m + 1):
        if i + k > n:
            break
        block = matches[i : i + k]

        # Generate feasible day assignments
        day_assignments = generate_assignments(block, stadiums)
        if not day_assignments:
            # no valid single-day arrangement for this block => skip
            continue

        # if dp[i+k] is feasible, combine
        if dp[i + k] is not None:
            for assignment in day_assignments:
                candidate = [assignment] + dp[i + k]
                if best is None or len(candidate) < len(best):
                    best = candidate

    return best

# --------------------------------------------------
# Main DP function to schedule all matches
# ------------------------------------------------------------
def schedule_matches(matches: List[Match], num_stadiums: int) -> Optional[Schedule]:
    """
    Build a minimal day-schedule for 'matches' with up to num_stadiums stadiums per day.
    If not feasible, returns None.
    """
    n = len(matches)
    # Create the stadiums
    stadiums = [Stadium(f"s{i+1}", f"Stadium {i+1}") for i in range(num_stadiums)]

    # dp[i]: best schedule from matches i..end
    dp: List[Optional[Schedule]] = [None]*(n+1)
    dp[n] = []  # if no matches remain => empty schedule

    # fill dp in descending order
    for i in range(n-1, -1, -1):
        dp[i] = get_optimizing_solution(i, dp, matches, stadiums)

    return dp[0]

# Helper to create a list of matches
#   --------------------------------------------------
def create_matches(length: int) -> List[Match]:
    """
    For example, length=3 => [(1,2), (3,4), (5,6)].
    """
    return [(2*i+1, 2*i+2) for i in range(length)]

# --------------------------------------------------
# Prim's algorithm to find the MST transporation network to connect stadiums
# --------------------------------------------------
def prim_mst(stadiums: List[str], distances: Dict[Tuple[str, str], float]) -> Tuple[float, List[Tuple[str, str]]]:
    """
    Compute the minimal spanning tree (MST) for the tournment given 5 
    stadiums roads connectivity. 
    
    """
    
    num_stadiums = len(stadiums)
    visited = {stadium: False for stadium in stadiums}
    min_heap = [(0, stadiums[0], stadiums[0])]  # (cost, from, to)
    mst = []
    total_cost = 0

    while min_heap and len(mst) < num_stadiums - 1:
        cost, frm, to = heapq.heappop(min_heap)
        if not visited[to]:
            visited[to] = True
            total_cost += cost
            if frm != to:
                mst.append((frm, to))
            for neighbor in stadiums:
                if not visited[neighbor] and (to, neighbor) in distances:
                    heapq.heappush(min_heap, (distances[(to, neighbor)], to, neighbor))
                elif not visited[neighbor] and (neighbor, to) in distances:
                    heapq.heappush(min_heap, (distances[(neighbor, to)], to, neighbor))

    return total_cost, mst

# --------------------------------------------------
# Build and print the stadium transporation network
# --------------------------------------------------
def build_stadium_network(stadiums: List[str]):
    """Compute and print MST for the given 5 stadiums roads connectivity."""
    distances = {
        ('s1', 's2'): 5,
        ('s1', 's3'): 10,
        ('s1', 's4'): 15,
        ('s1', 's5'): 20,
        ('s2', 's3'): 25,
        ('s2', 's4'): 20,
        ('s2', 's5'): 15,
        ('s3', 's4'): 10,
        ('s3', 's5'): 5,
        ('s4', 's5'): 10
    }
    try:
        total_cost, mst = prim_mst(stadiums, distances)
        print("\n====== MINIMAL STADIUMS ROADS NETWORK (MST) ====")
        print(f"Total length of roads network : {total_cost:.2f} miles")
        for s1, s2 in mst:
            print(f" - {s1} connected to {s2}")
    except ValueError as e:
        print(f"Error: {e}")
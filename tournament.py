import random
from schedule import schedule_matches

class Tournament:
    """
    A class that organizes the entire tournament.
    It uses dictionaries for team data.
    """

    def __init__(self, num_teams, num_stadiums, user_budget):
        """
        num_teams must be a multiple of 4 (4, 8, 12, 16, etc.).
        
          1) num_teams is an integer
          2) num_teams >= 4
         
        """
        if not isinstance(num_teams, int):
            raise ValueError("Number of teams must be an integer.")

        if num_teams < 4:
            raise ValueError("Number of teams must be >= 4.")

        if num_teams % 4 != 0:
            raise ValueError("Number of teams must be a multiple of 4.")

        self.num_teams = num_teams
        self.num_stadiums = num_stadiums
        self.user_budget = user_budget
        self.teams = []                # list of dictionaries
        self.final_standings_per_group = []
        self.qualified_for_stage2 = []
        self.stadiums = [f"s{i+1}" for i in range(num_stadiums)]
        
    # ------------------------------------------------------------------------
    # 1) Create Teams
    # -------------------------------------------------------------------------
    def create_teams(self):
        """
        Create the team dictionaries, each with:
          - name   
          - level ('A','B','C','D')
          - points (int)
          - group (int or None)
          - rank  (int or None)
          - prize (float)
        distribute levels evenly, then shuffle assignment.
        """
        levels = ["A"] * (self.num_teams // 4) \
               + ["B"] * (self.num_teams // 4) \
               + ["C"] * (self.num_teams // 4) \
               + ["D"] * (self.num_teams // 4)
        random.shuffle(levels)

        for i in range(1, self.num_teams + 1):
            self.teams.append({
                'name': f"Team {i}",
                'level': levels[i - 1],
                'points': 0,
                'group': None,
                'rank': None,
                'prize': 0.0  # Initialize prize to 0.0
            })

    # ----------------------------------------------------------------------
    # 2) Run Group Stage (specialized sort + grouping + round-robin)
    # -------------------------------------------------------------------------
    def run_group_stage(self):
        """
        (a) Sort teams by level => form groups => each group has one from A,B,C,D.
        (b) within each group, each team plays a round robin (3 matches/team).
        (c) sort each group by descending points, tie-break on name.
        (d) Assign group # and rank for reference in knockout stage.
        """
        # Sort by level so that A < B < C < D
        sorted_by_level = sorted(self.teams, key=lambda t: t['level'])

        # Partition by level
        levelA = [t for t in sorted_by_level if t['level'] == "A"]
        levelB = [t for t in sorted_by_level if t['level'] == "B"]
        levelC = [t for t in sorted_by_level if t['level'] == "C"]
        levelD = [t for t in sorted_by_level if t['level'] == "D"]

        # Build groups: each with [A, B, C, D]
        groups = []
        while levelA and levelB and levelC and levelD:
            group = [levelA.pop(), levelB.pop(), levelC.pop(), levelD.pop()]
            groups.append(group)

        # Round-robin in each group
        group_index = 1
        for group in groups:
            # Reset points to 0
            for tm in group:
                tm['points'] = 0

            print(f"\n==== GROUP {group_index} STAGE MATCHES ===")
            # 4 teams => 6 distinct matches
            matchups = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
            matches = [(group[i], group[j]) for (i, j) in matchups]
            match_tuples = [(i, j) for (i, j) in matchups]

            # Generate the schedule for the group matches
            schedule = schedule_matches(match_tuples, self.num_stadiums)

            if schedule is None:
                print("No valid schedule found for the group stage.")
                continue

            for day_schedule in schedule:
                for stadium_id, match in day_schedule.items():
                    teamA, teamB = group[match[0]], group[match[1]]
                    scoreA = random.randint(0, 5)
                    scoreB = random.randint(0, 5)
                    print(f"Match: {teamA['name']}(L:{teamA['level']}) vs "
                          f"{teamB['name']}(L:{teamB['level']}) at {stadium_id} => {scoreA}-{scoreB}")

                    self.determine_winner(scoreA, scoreB, teamA, teamB)

            # Now sort by (-points, name)
            sorted_group = sorted(
                group,
                key=lambda t: (-t['points'], t['name'])
            )

            print("\n-- FINAL GROUP STANDINGS --")
            rank_counter = 1
            for tm in sorted_group:
                tm['group'] = group_index
                tm['rank'] = rank_counter
                print(f" {rank_counter}) {tm['name']}, Points = {tm['points']}")
                rank_counter += 1

            self.final_standings_per_group.append(sorted_group)
            group_index += 1

        # After group stage => do the awarding
        print("\n===== First Stage Awards ====")
        self.award_budget_greedy()

        # After building and sorting groups, pick top 2 from each group
        self.qualified_for_stage2 = []
        for g_idx, grp in enumerate(self.final_standings_per_group, start=1):
            top1 = grp[0]
            top2 = grp[1]
            print(f"\n==> Group {g_idx} Qualifiers: {top1['name']}, {top2['name']}")
            self.qualified_for_stage2.append([top1, top2])

    def award_budget_greedy(self):
        """
        Ask for user_budget => rank1 => 50% => share equally among 
        all rank=1 teams across groups
        rank2 => 30%, rank3 =>15%, rank4 =>5%
        We'll incorporate 'augment_greedily' to demonstrate a local approach 
        (but no lumps).
        """
        rank_shares = {1: 0.50, 2: 0.30, 3: 0.15, 4: 0.05}

        # gather all teams in rank=1 across all groups, then pass them
        for r in [1, 2, 3, 4]:
            # gather all teams that have rank r
            rank_teams = []
            for g in self.final_standings_per_group:
                found = [tm for tm in g if tm['rank'] == r]
                rank_teams.extend(found)
            if not rank_teams:
                continue
            portion = rank_shares[r] * self.user_budget
            # call augment_greedily => we do single pass distributing 'portion' across rank_teams
            self.augment_greedily(rank_teams, portion)
    
    
    def augment_greedily(self, rank_teams, portion):
        """
        local, no-backtracking step to distribute 'portion' among rank_teams 
        in a single pass. We'll do an equal share approach:
          each team gets portion / len(rank_teams).
        This is "greedy" in the sense that once we commit
        rank #1's portion, we do not revise it if rank #2 
        or #3 might need more or less.
        """
        if not rank_teams:
            return
        
        share_each = portion / len(rank_teams)
        
        for tm in rank_teams:
            tm['prize'] += share_each
            rank_str = self.ordinal(tm['rank'])
            print(f"{tm['name']} {rank_str} in group {tm['group']} awarded ${share_each:.2f}")

    # --------------------------------------------------------------------------
    # match Logic (simulate match, awarding points)
    #
    def determine_winner(self, scoreA, scoreB, teamA, teamB):
        """
        If scoreA > scoreB ,teamA gets 3 points, else teamB gets 3 points, or tie=1 each
        """
        if scoreA > scoreB:
            teamA['points'] += 3
        elif scoreB > scoreA:
            teamB['points'] += 3
        else:
            teamA['points'] += 1
            teamB['points'] += 1

    # 
    # 3) Create Knockout Matches (like second stage)
    # -------------------------------------------------------------------------
    def create_knockout_matches(self):
        """
        Pair group i's 1st vs group i+1's 2nd, and group i's 2nd vs group i+1's 1st.
        returns a list of match pairs (teamA, teamB).
        """
        matches = []
        # self.qualified_for_stage2 is a list of 2-element sublists => [[top1, top2], [top1, top2], ...]
        for i in range(0, len(self.qualified_for_stage2), 2):
            if i+1 < len(self.qualified_for_stage2):
                grp1 = self.qualified_for_stage2[i]
                grp2 = self.qualified_for_stage2[i+1]
                matches.append((grp1[0], grp2[1]))  # (1st of g1 vs 2nd of g2)
                matches.append((grp1[1], grp2[0]))  # (2nd of g1 vs 1st of g2)
            else:
                # leftover => can give a bye or skip
                pass
        return matches

    # -------------------------------------------------------------------------
    # 4) Simulate Stage 2 or beyond
    # -------------------------------------------------------------------------
    def simulate_match(self, teamA, teamB):
        """
         method to return a random match result (scoreA, scoreB)
        
        """
        scoreA = random.randint(0,5)
        scoreB = random.randint(0,5)
        return scoreA, scoreB

    def run_matches(self, matches, stage_name="STAGE 2"):
        """
        For each pair, determine a winner, printing a custom format that includes rank+group.
        Return a list of winners
        """
        print(f"\n==== {stage_name} KNOCKOUT MATCHES ====")
        winners = []
        for (teamA, teamB) in matches:
            # simulate random result
            scoreA, scoreB = self.simulate_match(teamA, teamB)

            # rank in words
            a_rank_str = self.ordinal(teamA['rank'])
            b_rank_str = self.ordinal(teamB['rank'])

            print(f"{teamA['name']} {a_rank_str} in group {teamA['group']} vs "
                  f"{teamB['name']} {b_rank_str} in group {teamB['group']} => {scoreA}-{scoreB}",
                  end=" ")

            # pick winner or tie => random
            if scoreA > scoreB:
                print(f"-> Winner: {teamA['name']}")
                winners.append(teamA)
            elif scoreB > scoreA:
                print(f"-> Winner: {teamB['name']}")
                winners.append(teamB)
            else:
                # tie
                winner = random.choice([teamA, teamB])
                print(f"-> Tie! Random winner: {winner['name']}")
                winners.append(winner)
        return winners

    def ordinal(self, rank):
        """Helper to convert numeric rank to text form."""
        if rank == 1:
            return "first"
        elif rank == 2:
            return "second"
        elif rank == 3:
            return "third"
        elif rank == 4:
            return "fourth"
        return f"#{rank}"

    # -------------------------------------------------------------------------
    # 5) Final Knockout
    # -------------------------------------------------------------------------
    def run_final_knockout(self, teams):
        """
        repeated pairing, random shuffle each round, picking winners until 1 champion remains.
        """
        current = list(teams)
        random.shuffle(current)

        while len(current) > 1:
            print("\n==== KNOCKOUT SINGLE ELiMINATION ====")
            if len(current) % 2 == 1:
                bye = current.pop()
                print(f"{bye['name']} gets a bye automatically.")
                pass_list = [bye]
            else:
                pass_list = []

            # Pair up
            next_round_winners = []
            for i in range(0, len(current), 2):
                teamA = current[i]
                teamB = current[i+1]
                scoreA, scoreB = self.simulate_match(teamA, teamB)
                print(f"{teamA['name']} vs {teamB['name']} => {scoreA}-{scoreB}", end=" ")
                if scoreA > scoreB:
                    print(f"-> Winner: {teamA['name']}")
                    next_round_winners.append(teamA)
                elif scoreB > scoreA:
                    print(f"-> Winner: {teamB['name']}")
                    next_round_winners.append(teamB)
                else:
                    # tie
                    winner = random.choice([teamA, teamB])
                    print(f"-> Tie! Random winner: {winner['name']}")
                    next_round_winners.append(winner)

            new_field = next_round_winners + pass_list
            random.shuffle(new_field)
            current = new_field

        return current[0]  # champion

    # -----------------------------------------
    # Overarching run method
    # -------------------------------------------
    def run_tournament(self):
        """
        Orchestrate the entire tournament:
          1) create_teams
          2) group stage
          3) stage 2 (knockout matches)
          4) final knockout
        """
        self.create_teams()

        print("\n=== INITIAL TEAMS ===")
        for tm in self.teams:
            print(tm)

        # group stage 
        self.run_group_stage()
        if len(self.final_standings_per_group) == 1:
            # Only one group => top 2 from that single group
            # This effectively bypasses "Stage 2" pairing logic
            stage2_winners = self.final_standings_per_group[0][:2]
        else:
            # STAGE 2
            stage2_pairs = self.create_knockout_matches()
            stage2_winners = self.run_matches(stage2_pairs, "STAGE 2")

        # FINAL kNOCKOUT
        champion = self.run_final_knockout(stage2_winners)
        print(f"\n* CHAMPION: {champion['name']} ***")






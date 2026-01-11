from tournament import Tournament
from schedule import build_stadium_network

def main():
    while True:
        stadium_count = input("number of stadiums will host the tournament: ")
        team_count = input("Enter the number of teams (multiple of 4): ")
        user_budget = input("Enter the total award budget for the Groups Stage: ")
        try:
            num_teams = int(team_count)
            num_stadiums = int(stadium_count)
            user_budget = float(user_budget)
            # The constructor checks further constraints.
            tour = Tournament(num_teams, num_stadiums, user_budget)
            break
        except ValueError as e:
            print(f"Invalid input: {e}")

    # Build and print the stadium network
    build_stadium_network(tour.stadiums)

    # Create the tournament
    tour.run_tournament()

if __name__ == "__main__":
    main()



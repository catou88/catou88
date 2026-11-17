#!/usr/bin/env python3
"""Fetch live GitHub stats for the profile cards -> data/stats.json.

Needs GH_TOKEN (or GITHUB_TOKEN) in the environment. Uses only the standard
library so the workflow needs no installs.

Lifetime contributions and commits are summed across every contribution
year. Private contributions are counted only when the token is a personal
access token from the profile owner (see README).
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors"):
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]


def main():
    if not TOKEN:
        raise SystemExit("Set GH_TOKEN or GITHUB_TOKEN")
    login = json.load(open(os.path.join(ROOT, "profile.json")))["login"]

    base = gql("""
      query($login:String!){ user(login:$login){
        repositories(ownerAffiliations:OWNER, privacy:PUBLIC){ totalCount }
        pullRequests{ totalCount }
        repositoriesContributedTo(includeUserRepositories:false,
          contributionTypes:[COMMIT, PULL_REQUEST, REPOSITORY]){ totalCount }
        contributionsCollection{
          contributionYears
          contributionCalendar{ weeks{ contributionDays{ contributionCount } } }
        }
      }}""", login=login)["user"]

    total_contrib = total_commits = 0
    for year in base["contributionsCollection"]["contributionYears"]:
        y = gql("""
          query($login:String!,$from:DateTime!,$to:DateTime!){ user(login:$login){
            contributionsCollection(from:$from,to:$to){
              totalCommitContributions restrictedContributionsCount
              contributionCalendar{ totalContributions }
            }}}""", login=login, **{"from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"})
        cc = y["user"]["contributionsCollection"]
        total_contrib += cc["contributionCalendar"]["totalContributions"]
        total_commits += cc["totalCommitContributions"] + cc["restrictedContributionsCount"]

    weeks = [sum(d["contributionCount"] for d in w["contributionDays"])
             for w in base["contributionsCollection"]["contributionCalendar"]["weeks"]]

    stats = {
        "total_contributions": total_contrib,
        "total_commits": total_commits,
        "pull_requests": base["pullRequests"]["totalCount"],
        "public_repos": base["repositories"]["totalCount"],
        "repos_contributed_to": base["repositoriesContributedTo"]["totalCount"],
        "weeks": weeks,
    }
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    print({k: v for k, v in stats.items() if k != "weeks"}, file=sys.stderr)


if __name__ == "__main__":
    main()

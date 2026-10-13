# Product Requirements - IRCTC PNR Notifier

## Problem
Travelers want to know when a waitlisted or RAC ticket improves without repeatedly checking PNR status manually.

## Users
A traveler monitoring one or more PNRs for their own bookings.

## Goal
Check configured PNRs on a schedule and notify the user about meaningful status improvements.

## MVP
- Accept one or more validated 10-digit PNRs through environment configuration or CLI.
- Fetch and normalize PNR status from a configured provider.
- Detect waitlist-position improvements, transition to RAC, and transition to CNF.
- Send alerts through configured notification adapters.
- Retain state privately between runs where persistence is configured.
- Provide deterministic unit tests with mocked provider responses.

## Out of scope
- Public multi-user web dashboard.
- Storing passenger names or other unnecessary personal data.
- Guaranteeing confirmation or predicting confirmation probability.
- Claiming instant alerts from a five-hour scheduled poll.
- Bypassing provider access controls, quotas, or terms.

## Success criteria
- No real PNRs or API credentials are hard-coded in tracked files.
- Unknown or malformed provider data does not trigger a false improvement alert.
- A failed notification does not advance the stored baseline for that improvement.
- Corrupt state fails visibly instead of resetting silently.
- Tests run without live APIs or outbound notification calls.

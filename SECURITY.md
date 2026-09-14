# Security Policy

## Supported versions

There are no tagged releases yet — only the latest commit on `main` is supported.

## Reporting a vulnerability

Please report security issues privately using GitHub's [private vulnerability reporting](https://github.com/beyondpratham/Assembler-Simulator/security/advisories/new) (Security tab → Report a vulnerability) instead of opening a public issue.

## Scope

The web app (`invoke run`) is a local development tool meant to run on `localhost` only. It has no authentication and is not hardened for exposure on a public network — don't bind it to a public interface or deploy it as-is.

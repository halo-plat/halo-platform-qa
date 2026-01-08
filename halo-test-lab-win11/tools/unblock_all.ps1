# Unblock all PowerShell scripts in this repo (removes Mark-of-the-Web)
Get-ChildItem -Recurse -Filter *.ps1 | Unblock-File

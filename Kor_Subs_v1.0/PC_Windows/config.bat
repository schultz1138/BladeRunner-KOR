::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCyDJGyX8VAjFBddSQaHAE+1EbsQ5+n//NaErUMbXeVxcYzUug==
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSzk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+JeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCyDJGyX8VAjFBddSQaHAE+1EbsQ5+n//NakrUMbXeVxfZfeug==
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off

:: ?ÑÏû¨ Î∞∞Ïπò ?åÏùº???àÎäî ?¥ÎçîÎ•??ëÏóÖ Í≤ΩÎ°úÎ°??§Ï†ï
cd /d "%~dp0"

:: ?∏Ïù¥Î∏??¥ÎçîÍ∞Ä ?ÜÏúºÎ©??ùÏÑ±
if not exist "Saved Games" (
    mkdir "Saved Games"
)

:: ScummVM ?§Ìñâ
start "" "scummvm.exe" ^
    -c "scummvm.ini" ^
    --path="." ^
    --savepath=".\Saved Games"

exit
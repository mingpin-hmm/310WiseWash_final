# 310 WiseWash final
Wisewash helps users find out the best day to wash their cars, solving the frustation of washing their car and having it get dirty again by the rain right after. The application analyzes a 5 day forecast of rain and pollen data, provides a YES/NO answer whether to wash today, and if not, when the next best day is. 
Our original project proposal aimed to process a 14 day forecast but due to limitations in the Accuweather API in the free tier, the forecast is reduced to 5 days.

HOW TO GET API KEY:
A key from Accuweather is required to use the API, Open meteo does not need an key.
1. Go to Accuweather developers portal https://developer.accuweather.com/
2. Click "Register" to create a free account.
3. Once logged in, go to "Subscriptions and keys" and create a key.
5. Once created, click on your app to view your API Key. Copy this string.

Inside the project folder, create a file called "keys.py" and paste your key
ACCUWEATHER_API_KEY = "PASTE_YOUR_ACCUWEATHER_KEY_HERE"

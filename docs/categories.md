# The database

This is the layout (and the possible categories) for the database entries. When storing guesses, the appropriate form must be used, as well as upon asking for it.


- Timestamp
- Author
- Event:
    - FreePractice1:
        - FirstPlace: *FP1*
    - FreePractice2:
        - FirstPlace: *FP2*
    - FreePractice3: 
        - FirstPlace: *FP3*

    - Qualification (Q3):
        - FirstPlace: *Q1st*
        - SecondPlace: *Q2nd*
        - ThirdPlace: *Q3rd*
        - BestOfTheRest: *Q-BOTR*

    - Race:
        - FirstPlace: *R1st*
        - SecondPlace: *R2nd*
        - ThirdPlace: *R3rd*
        - BestOfTheRest: *R-BOTR*
        - DriverOfTheDay: *R-DOTD*
        - FastestLap: *R-F*
        - NumberofDNF: *R-DNF*
- Guess:
  - String: name

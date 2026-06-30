# Study Scheduling with Answer Set Programming

A study scheduling application built with **Python**, **Streamlit**, and **Answer Set Programming (ASP)** using **Clingo**. The application generates personalized study schedules based on subjects, priorities, difficulty, deadlines, and weekly availability.

## Features

* Add and manage multiple subjects
* Assign:
  * Difficulty level (1–5)
  * Priority (1–5)
  * Subject strength (1–5)
* Set deadlines for each subject
* Configure weekly availability (morning, afternoon, evening)
* Customize study session duration
* Generate optimized study schedules using **Answer Set Programming (ASP)** and **Clingo**
* View the generated study schedule in a calendar
* Upload multiple students through a JSON file
* Automatically convert JSON data into ASP facts


## Technologies Used

* Python
* Streamlit
* Clingo (Answer Set Programming Solver)
* Pandas
* JSON
* Streamlit Calendar

## How It Works

1. Enter the subjects you want to study.
2. Assign each subject:
   * Difficulty
   * Priority
   * Strength
3. Add deadlines.
4. Specify your weekly availability.
5. Generate a personalized study schedule.
6. The application converts your input into ASP facts and uses **Clingo** to compute an optimized schedule that satisfies the defined constraints.
7. View the generated study schedule in a calendar.

## Students Scheduling

The application also supports scheduling for multiple students.

Using the **Students** page, you can:

* Upload a JSON file containing student information.
* Automatically convert the data into ASP facts.
* Generate schedules using the ASP solver.
* View the generated solution directly in the application.

## Example Students JSON

```json
[
  {
    "id": 1,
    "subjects": [
      {
        "name": "bsp4",
        "difficulty": 5,
        "priority": 4,
        "strength": 2
      }
    ],
    "availability": [
      {
        "day": "monday",
        "time": "morning",
        "hours": 2
      }
    ],
    "avoid": [
      { "day": "monday", "time": "afternoon" },
      { "day": "monday", "time": "evening" }
    ],
    "split": []
  }
]
```

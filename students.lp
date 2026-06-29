
% HOURS
hour(St,D,T,I) :-
    available(St,D,T,H),
    I = 1..H.

% STUDY ASSIGNMENT
0 { study(St,S,D,T,I) : subject(St,S) } 1 :- hour(St,D,T,I).


% SPLIT LOGIC

% if split exists, use it
slot_capacity(St,D,T,MS) :-
    split(St,D,T,MS).

% if no split, only one subject
slot_capacity(St,D,T,1) :-
    available(St,D,T,_),
    not split(St,D,T,_).

% track used subjects
used_subject(St,D,T,S) :-
    study(St,S,D,T,_).

% cannot exceed capacity
:- slot_capacity(St,D,T,MS),
   #count { S : used_subject(St,D,T,S) } > MS.

% if split exists, exactly MS subjects
:- split(St,D,T,MS),
   #count { S : used_subject(St,D,T,S) } != MS.

% impossible split
:- split(St,D,T,MS),
   available(St,D,T,H),
   MS > H.


% REQUIRED HOURS
required_hours(St,S,H) :-
    student(St),
    subject(St,S),
    difficulty(St,S,E),
    priority(St,S,P),
    subject_strength(St,S,W),
    H = E + P + (6 - W).


% TOTAL STUDY HOURS
study_hours(St,S,H) :-
    student(St),
    subject(St,S),
    H = #sum { 1,D,T,I : study(St,S,D,T,I) }.

% WEEKLY CAPACITY
weekly_capacity(St,H) :-
    student(St),
    H = #count { D,T,I : hour(St,D,T,I) }.

% WEEKS NEEDED
weeks_needed(St,S,W) :-
    student(St),
    subject(St,S),
    required_hours(St,S,H),
    weekly_capacity(St,C),
    W = (H + C - 1) / C.


% exact required hours
:- required_hours(St,S,Req),
   study_hours(St,S,Got),
   Got != Req.



% SOFT PENALTY
#minimize {
    1,St,S,D,T,I :
    study(St,S,D,T,I),
    avoid(St,D,T)
}.

% OPTIMIZATION
#maximize {
    (P - W)@2,St,S,D,T,I :
    study(St,S,D,T,I),
    priority(St,S,P),
    subject_strength(St,S,W)
}.


% OUTPUT
#show study/5.
#show required_hours/3.
#show study_hours/3.







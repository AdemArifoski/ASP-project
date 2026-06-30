
% HOURS 
hour(D,T,I) :-
    available(D,T,H),
    I = 1..H.

% STUDY ASSIGNMENT
0 { study(S,D,T,I) : subject(S) } 1 :- hour(D,T,I).


% SPLIT LOGIC

% if split exists, use it
slot_capacity(D,T,MS) :-
    split(D,T,MS).

% if no split, only 1 subject allowed
slot_capacity(D,T,1) :-
    available(D,T,_),
    not split(D,T,_).

% track which subjects are used in a slot
used_subject(D,T,S) :-
    study(S,D,T,_).

% do not exceed capacity
:- slot_capacity(D,T,MS),
   #count { S : used_subject(D,T,S) } > MS.

% if split is defined, must use exactly MS subjects
:- split(D,T,MS),
   #count { S : used_subject(D,T,S) } != MS.

% prevent impossible splits
:- split(D,T,MS),
   available(D,T,H),
   MS > H.


% REQUIRED HOURS
required_hours(S,H) :-
    difficulty(S,E),
    priority(S,P),
    subject_strength(S,W),
    H = E + P + (6 - W).


% TOTAL STUDY HOURS
study_hours(S,H) :-
    subject(S),
    H = #sum { 1,D,T,I : study(S,D,T,I) }.


% WEEKLY CAPACITY
weekly_capacity(H) :-
    H = #count { D,T,I : hour(D,T,I) }.


% WEEKS NEEDED
weeks_needed(S,W) :-
    required_hours(S,H),
    weekly_capacity(C),
    W = (H + C - 1) / C.


% exact required hours
:- required_hours(S,Req),
   study_hours(S,Got),
   Got != Req.


% SOFT PENALTY FOR AVOID
#minimize {
    1,S,D,T,I :
    study(S,D,T,I),
    avoid(D,T)
}.


% OPTIMIZATION
#maximize {
    (P - W), S,D,T,I :
    study(S,D,T,I),
    priority(S,P),
    subject_strength(S,W)
}.


% OUTPUT
#show study/4.
#show required_hours/2.
#show study_hours/2.
#show weeks_needed/2.
#show split/3.









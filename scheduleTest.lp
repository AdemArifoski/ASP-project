% =========================
% CHOOSE NUMBER OF BLOCKS
% =========================
possible_blocks(D,T,1) :- available(D,T,_).
possible_blocks(D,T,B) :- split(D,T,B).

1 { use_blocks(D,T,B) : possible_blocks(D,T,B) } 1 :-
    available(D,T,_).

% =========================
% GENERATE BLOCKS
% =========================
block(D,T,I) :-
    use_blocks(D,T,B),
    I = 1..B.

% =========================
% HOURS PER BLOCK
% =========================
block_hours(D,T,Hb) :-
    available(D,T,H),
    use_blocks(D,T,B),
    Hb = H / B.

% =========================
% STUDY CHOICE (per block)
% =========================
0 { study(S,D,T,I) : subject(S) } 1 :-
    block(D,T,I).

% =========================
% REQUIRED HOURS
% =========================
required_hours(S,H) :-
    difficulty(S,E),
    priority(S,P),
    subject_strength(S,W),
    H = E + P + (6 - W).

% =========================
% TOTAL STUDY HOURS
% =========================
study_hours(S,H) :-
    subject(S),
    H = #sum {
        Hb,D,T,I :
        study(S,D,T,I),
        block_hours(D,T,Hb)
    }.

% =========================
% WEEKLY CAPACITY
% =========================
weekly_capacity(H) :-
    H = #sum {
        Hb,D,T,I :
        block(D,T,I),
        block_hours(D,T,Hb)
    }.

% =========================
% TOTAL REQUIRED
% =========================
total_required(H) :-
    H = #sum {
        X,S : required_hours(S,X)
    }.

% =========================
% WEEKS NEEDED
% =========================
weeks_needed(W) :-
    total_required(H),
    weekly_capacity(C),
    W = (H + C - 1) / C.



block_info(D,T,I,Hb) :-
    block(D,T,I),
    block_hours(D,T,Hb).


% =========================
% CONSTRAINTS
% =========================

% do not exceed required hours
:- required_hours(S,Req),
   study_hours(S,Got),
   Got > Req.

% =========================
% SOFT PENALTY FOR AVOID
% =========================
#minimize {
    Hb@1, S,D,T,I :
    study(S,D,T,I),
    avoid(D,T),
    block_hours(D,T,Hb)
}.

% =========================
% OPTIMIZATION
% =========================
#maximize {
    Hb*(P - W)@2, S,D,T,I :
    study(S,D,T,I),
    block_hours(D,T,Hb),
    priority(S,P),
    subject_strength(S,W)
}.

% =========================
% OUTPUT
% =========================
#show study/4.
%#show use_blocks/3.
%#show study_hours/2.
#show weeks_needed/1.
%#show block_info/4.











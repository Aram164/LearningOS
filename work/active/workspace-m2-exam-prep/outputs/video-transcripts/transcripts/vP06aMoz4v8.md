---
video_id: vP06aMoz4v8
url: https://www.youtube.com/watch?v=vP06aMoz4v8
title: Machine Learning Fundamentals: Sensitivity and Specificity
channel: StatQuest with Josh Starmer
duration: 11:46
language: en
unit: L01
status: OK
---

[00:00] when the well runs dry you might be
[00:04] thirsty but this still StatQuest you
[00:07] can watch it StatQuest hello I'm Josh
[00:13] Starmar and welcome to StatQuest today
[00:15] we're gonna continue our series on
[00:17] machine learning fundamentals and we're
[00:19] going to talk about sensitivity and
[00:21] specificity they're gonna be clearly
[00:23] explained this StatQuest follows up on
[00:27] the one that describes the confusion
[00:29] matrix so if you're not already down
[00:31] with that
[00:32] check out the quest the first half of
[00:35] this video will explain how to calculate
[00:37] and interpret sensitivity and
[00:40] specificity when you have a confusion
[00:42] matrix with two rows and two columns and
[00:45] the second half will show you how to
[00:47] calculate and interpret sensitivity and
[00:50] specificity when you have three or more
[00:52] rows and columns
[00:55] even if you're already down with the
[00:57] confusion matrix let's remember that
[00:59] rows correspond to what was predicted
[01:01] and columns correspond to the known
[01:05] truth when there are only two categories
[01:09] to choose from in this case the two
[01:11] choices were has heart disease or does
[01:14] not have heart disease then the top
[01:17] left-hand corner contains the true
[01:19] positives true positives are patients
[01:23] that had heart disease that were also
[01:25] predicted to have heart disease true
[01:29] negatives are in the bottom right hand
[01:30] corner true negatives are patients that
[01:34] did not have heart disease and were
[01:36] predicted not to have heart disease the
[01:40] bottom left-hand corner contains the
[01:42] false negatives false negatives are when
[01:45] a patient has heart disease but the
[01:48] prediction said they didn't lastly the
[01:52] top right hand corner contains the false
[01:54] positives false positives are patients
[01:57] that do not have heart disease but the
[01:59] prediction says that they do once we
[02:03] filled out the confusion matrix we can
[02:05] calculate two useful metrics sensitivity
[02:09] and specificity in this case sensitivity
[02:13] tells us what percentage of patients
[02:15] with heart disease were correctly
[02:18] identified
[02:20] sensitivity is the true positives
[02:23] divided by the sum of the true positives
[02:26] and the false negatives
[02:29] specificity tells us what percentage of
[02:32] patients without heart disease were
[02:34] correctly identified specificity are the
[02:39] true negatives divided by the sum of the
[02:42] true negatives and the false positives
[02:46] in the StatQuest on the confusion
[02:48] matrix we applied logistic regression to
[02:51] a testing data set and ended up with
[02:55] this confusion matrix let's start by
[02:59] calculating sensitivity for this
[03:01] logistic regression here's the formula
[03:05] for sensitivity and for true positives
[03:08] we plug in 139 and for false negatives
[03:13] we plug in 32 when we do the math we get
[03:18] zero point eight one sensitivity tells
[03:22] us that 81% of the people with heart
[03:25] disease were correctly identified by the
[03:27] logistic regression model
[03:30] now let's calculate the specificity
[03:34] here's the formula for specificity and
[03:37] for true negatives we will plug in 112 and
[03:42] for false positives we will plug in 20 when
[03:47] we do the math we get 0.85 specificity
[03:52] tells us that 85% of the people without
[03:55] heart disease were correctly identified
[03:58] by the logistic regression model now
[04:02] let's calculate sensitivity and
[04:03] specificity for the random forest model
[04:06] that we used in the confusion matrix
[04:08] StatQuest
[04:10] here's the confusion matrix here's the
[04:14] formula for sensitivity and when we plug
[04:17] in the numbers we get zero point eight
[04:19] three
[04:21] here's the formula for specificity and
[04:24] when we plug in the numbers we get zero
[04:27] point eight three again
[04:30] now we can compare the sensitivity and
[04:33] specificity values that we calculated
[04:35] for the logistic regression to the
[04:38] values we calculated for the random
[04:40] forest
[04:42] sensitivity tells us that the random
[04:45] forest is slightly better at correctly
[04:47] identifying positives which in this case
[04:50] are patients with heart disease
[04:54] specificity tells us that logistic
[04:56] regression is slightly better correctly
[04:59] identifying negatives which in this case
[05:02] are patients without heart disease we
[05:06] would choose the logistic regression
[05:08] model
[05:08] if correctly identifying patients
[05:10] without heart disease was more important
[05:13] than correctly identifying patients with
[05:15] heart disease
[05:18] alternatively we would choose the random
[05:21] forest model if correctly identifying
[05:23] patients with heart disease was more
[05:26] important than correctly identifying
[05:28] patients without heart disease BAM
[05:33] in the confusion matrix stat quest we
[05:36] calculated this confusion matrix when we
[05:39] tried to predict someone's favorite movie
[05:42] now let's talk about how to calculate
[05:44] sensitivity and specificity when we have
[05:47] a confusion matrix with three rows and
[05:49] three columns the big difference when
[05:53] calculating sensitivity and specificity
[05:55] for larger confusion matrices is that
[05:59] there are no single values that work for
[06:01] the entire matrix instead we calculate a
[06:06] different sensitivity and specificity
[06:07] for each category
[06:11] so for this confusion matrix we'll need
[06:14] to calculate sensitivity and specificity
[06:16] for the movie troll 2 for the movie Gore
[06:20] police and for the movie cool as ice
[06:25] let's start by calculating sensitivity
[06:28] for troll 2 for troll 2 there were 12
[06:32] true positives people that were
[06:35] correctly predicted to love troll 2 more
[06:38] than Gore police and cool as ice
[06:41] so for true positives we'll plug in 12
[06:46] and there were 112 plus 83 which equals
[06:50] 195 false negatives people that love to
[06:55] troll 2 but were predicted to love
[06:57] Gore police or cool as ice
[07:00] so for false negatives will plug in 195
[07:04] and when we do the math we get 0.06
[07:11] sensitivity for troll 2 tells us that
[07:13] only 6% of the people that loved the
[07:16] movie troll 2 more than Gore police or
[07:19] cool as ice were correctly identified
[07:22] now let's calculate the specificity for
[07:25] troll 2 there were 23 plus 77 plus 92
[07:31] plus 17 equals 209 true negatives people
[07:36] that were correctly predicted to like
[07:38] Gore police or cool as ice more than
[07:41] troll 2 so for true negatives will plug
[07:45] in 209
[07:47] and there were 102 plus 93 equals 195
[07:52] false positives people that loved gore
[07:55] police or cool as ice the most but were
[07:59] predicted to love troll 2 so for false
[08:02] positives will plug in 195 and when we
[08:07] do the math we get 0.52 specificity
[08:12] for troll 2 tells us that 52% of the
[08:16] people who loved Gore police or cool as
[08:18] ice more than troll 2 were correctly
[08:21] identified
[08:23] calculating sensitivity and specificity
[08:26] for Gore police is very similar let's
[08:30] start by calculating sensitivity
[08:34] there are 23 true positives people that
[08:37] were correctly predicted to love Gore
[08:39] police the most
[08:42] and 102 plus 92 equals 194 false
[08:47] negatives people who loved Gore police
[08:50] the most but were predicted to love
[08:52] troll 2 or cool as ice more when we do the
[08:56] math we get 0.11 sensitivity
[09:01] for Gore police tells us that only 11%
[09:04] of the people that loved Gore police
[09:06] were correctly identified now let's
[09:10] calculate specificity there were 12 plus
[09:14] 93 plus 83 plus 17 equals 205 true
[09:19] negatives people correctly identified as
[09:22] loving troll 2 or cool as ice more than
[09:25] gore police
[09:27] and 112 plus 77 equals 189 false
[09:32] positives people predicted to love gore
[09:35] police even though they didn't and when
[09:39] we do the math we get 0.52 specificity
[09:44] for gore police tells us that 52% of the
[09:47] people that loved troll 2 or cool as
[09:50] ice more than gore police were correctly
[09:52] identified
[09:54] lastly calculating sensitivity and
[09:57] specificity for cool as ice follows the
[10:00] same steps we identify the true
[10:03] positives the false positives the true
[10:07] negatives and the false negatives and
[10:10] then plug in the numbers first for
[10:15] sensitivity then for specificity double bam
[10:20] if we had a confusion matrix with
[10:24] four rows and four columns then we would
[10:28] have to calculate sensitivity and
[10:29] specificity for four different
[10:31] categories little bam
[10:38] in summary sensitivity equals the true positives
[10:41] divided by the sum of the true positives
[10:44] and the false negatives and specificity
[10:48] equals the true negatives divided by the
[10:51] sum of the true negatives and the false
[10:53] positives we can use sensitivity and
[10:57] specificity to help us decide which
[11:00] machine learning method would be best
[11:02] for our data if correctly identifying
[11:06] positives is the most important thing to
[11:08] do with the data we should choose a
[11:10] method with higher sensitivity if
[11:13] correctly identifying negatives is more
[11:16] important then we should put more
[11:17] emphasis on specificity
[11:21] hooray we've made it to the end of
[11:23] another exciting StatQuest if you like
[11:26] this StatQuest and want to see more
[11:28] please subscribe and if you want to
[11:30] support stack quest well consider buying
[11:33] one or two of my original songs alright
[11:35] until next time quest on

---
video_id: _L39rN6gz7Y
url: https://www.youtube.com/watch?v=_L39rN6gz7Y
title: Decision and Classification Trees, Clearly Explained!!!
channel: StatQuest with Josh Starmer
duration: 18:08
language: en
unit: L12
status: OK
---

[00:00] i like decision trees how about
[00:03] i like decision trees how about you stat quest
[00:07] you stat quest hello i'm josh darmer and welcome to
[00:10] hello i'm josh darmer and welcome to statquest
[00:11] statquest today we're going to talk about decision
[00:13] today we're going to talk about decision and classification trees
[00:15] and classification trees and they're going to be clearly
[00:16] and they're going to be clearly explained here is a simple decision tree
[00:21] explained here is a simple decision tree if a person wants to learn about
[00:22] if a person wants to learn about decision trees
[00:24] decision trees then they should watch this stat quest
[00:27] then they should watch this stat quest in contrast
[00:28] in contrast if a person does not want to learn about
[00:30] if a person does not want to learn about decision trees
[00:32] decision trees then check out the latest justin bieber
[00:34] then check out the latest justin bieber video instead
[00:37] video instead in general a decision tree makes a
[00:39] in general a decision tree makes a statement
[00:40] statement and then makes a decision based on
[00:42] and then makes a decision based on whether or not that statement is true or
[00:44] whether or not that statement is true or false
[00:46] false it's no big deal when a decision tree
[00:49] it's no big deal when a decision tree classifies
[00:50] classifies things into categories it's called a
[00:53] things into categories it's called a classification tree
[00:55] classification tree and when a decision tree predicts
[00:57] and when a decision tree predicts numeric values
[00:59] numeric values it's called a regression tree in this
[01:02] it's called a regression tree in this case
[01:03] case we're using diet to predict a numeric
[01:06] we're using diet to predict a numeric value for mouse size
[01:09] value for mouse size note for the remainder of this video we
[01:12] note for the remainder of this video we are going to focus on classification
[01:14] are going to focus on classification trees
[01:15] trees however if you want to learn more about
[01:18] however if you want to learn more about regression trees
[01:19] regression trees fear not there's a whole stat quest
[01:22] fear not there's a whole stat quest dedicated to regression trees
[01:24] dedicated to regression trees the link is in the description below
[01:28] the link is in the description below now here's a more complicated
[01:30] now here's a more complicated classification tree
[01:33] classification tree it combines numeric data with yes
[01:36] it combines numeric data with yes no data so it's okay to mix data types
[01:40] no data so it's okay to mix data types in the same tree
[01:42] in the same tree also notice that the tree asks about
[01:45] also notice that the tree asks about exercising multiple times
[01:48] exercising multiple times and that the amount of time exercising
[01:50] and that the amount of time exercising isn't always the same
[01:53] isn't always the same so numeric thresholds can be different
[01:55] so numeric thresholds can be different for the same data
[01:57] for the same data lastly the final classifications can be
[02:00] lastly the final classifications can be repeated
[02:02] repeated for the most part classification trees
[02:05] for the most part classification trees are pretty easy to work with
[02:07] are pretty easy to work with you start at the top and work your way
[02:10] you start at the top and work your way down
[02:11] down and down until you get to a point where
[02:14] and down until you get to a point where you can't go any further
[02:16] you can't go any further and that's how you'll classify something
[02:19] and that's how you'll classify something note so far i've been labeling the
[02:22] note so far i've been labeling the arrows with true
[02:23] arrows with true or false but usually it is just
[02:26] or false but usually it is just assumed that if a statement is true you
[02:29] assumed that if a statement is true you go to the left
[02:31] go to the left and if a statement is false you go to
[02:33] and if a statement is false you go to the right
[02:35] the right so sometimes you see true and false
[02:37] so sometimes you see true and false labels
[02:38] labels sometimes you don't it's no big deal
[02:41] sometimes you don't it's no big deal oh no it's the dreaded terminology alert
[02:45] oh no it's the dreaded terminology alert the very top of the tree is called the
[02:48] the very top of the tree is called the root node
[02:48] root node or just the root these are called
[02:51] or just the root these are called internal nodes or branches
[02:54] internal nodes or branches branches have arrows pointing to them
[02:57] branches have arrows pointing to them and they have
[02:58] and they have arrows pointing away from them lastly
[03:01] arrows pointing away from them lastly these are called leaf nodes or just
[03:04] these are called leaf nodes or just leaves
[03:05] leaves leaves have arrows pointing to them but
[03:08] leaves have arrows pointing to them but there are no arrows pointing away from
[03:10] there are no arrows pointing away from them
[03:11] them bam now that we know how to use and
[03:14] bam now that we know how to use and interpret classification trees let's
[03:17] interpret classification trees let's learn how to build one from raw data
[03:21] learn how to build one from raw data this data tells us whether or not
[03:23] this data tells us whether or not someone loves popcorn
[03:25] someone loves popcorn whether or not they love soda their age
[03:29] whether or not they love soda their age and whether or not they love the 1991
[03:32] and whether or not they love the 1991 blockbuster
[03:33] blockbuster cool as ice starring vanilla ice
[03:37] cool as ice starring vanilla ice so we will use this data to build this
[03:40] so we will use this data to build this classification tree
[03:42] classification tree that predicts whether or not someone
[03:44] that predicts whether or not someone loves cool as ice
[03:47] loves cool as ice now pretend you've never seen this tree
[03:49] now pretend you've never seen this tree before
[03:50] before and let's see how to build a tree
[03:52] and let's see how to build a tree starting with just
[03:53] starting with just data the first thing we do is decide
[03:57] data the first thing we do is decide whether loves popcorn
[03:59] whether loves popcorn love soda or age should be the question
[04:02] love soda or age should be the question we ask
[04:02] we ask at the very top of the tree to make that
[04:05] at the very top of the tree to make that decision
[04:06] decision we'll start by looking at how well loves
[04:09] we'll start by looking at how well loves popcorn
[04:09] popcorn predicts whether or not someone loves
[04:12] predicts whether or not someone loves cool as ice
[04:14] cool as ice to do this we'll make a super simple
[04:16] to do this we'll make a super simple tree that only asks if someone loves
[04:19] tree that only asks if someone loves popcorn
[04:20] popcorn and then we'll run the data down the
[04:22] and then we'll run the data down the tree
[04:24] tree for example the first person in the
[04:26] for example the first person in the dataset
[04:27] dataset loves popcorn so they go to the leaf on
[04:30] loves popcorn so they go to the leaf on the left
[04:32] the left and because they do not love cool as ice
[04:36] and because they do not love cool as ice we'll keep track of that by putting a 1
[04:38] we'll keep track of that by putting a 1 under the word
[04:39] under the word no the second person in the data set
[04:43] no the second person in the data set also loves popcorn so they also go to
[04:47] also loves popcorn so they also go to the leaf on the left
[04:49] the leaf on the left and because they also do not love cool
[04:52] and because they also do not love cool as ice
[04:53] as ice we increment no to two
[04:56] we increment no to two the third person does not love popcorn
[05:00] the third person does not love popcorn so they go to the leaf on the right and
[05:03] so they go to the leaf on the right and because they love cool as ice
[05:05] because they love cool as ice we put a 1 under the word yes
[05:09] we put a 1 under the word yes likewise we run the remaining rows down
[05:11] likewise we run the remaining rows down the tree
[05:12] the tree keeping track of whether or not each one
[05:15] keeping track of whether or not each one loves
[05:15] loves cool as ice bam
[05:18] cool as ice bam now let's do the exact same thing for
[05:21] now let's do the exact same thing for love soda
[05:24] love soda at the two little trees we see that
[05:26] at the two little trees we see that neither one does a perfect
[05:28] neither one does a perfect job predicting who will and who will not
[05:31] job predicting who will and who will not love cool as ice specifically
[05:35] love cool as ice specifically these three leaves contain mixtures of
[05:37] these three leaves contain mixtures of people that do
[05:38] people that do and do not love cool as ice
[05:42] and do not love cool as ice dread it's another terminology alert
[05:45] dread it's another terminology alert because these three leaves all contain a
[05:48] because these three leaves all contain a mixture of people who do
[05:50] mixture of people who do and do not love cool as ice they are
[05:53] and do not love cool as ice they are called
[05:53] called impure in contrast
[05:57] impure in contrast this leaf only contains people who do
[05:59] this leaf only contains people who do not love cool as ice
[06:02] not love cool as ice because both leaves in the love's
[06:03] because both leaves in the love's popcorn tree
[06:05] popcorn tree are impure and only one leaf in the love
[06:08] are impure and only one leaf in the love soda tree is impure
[06:11] soda tree is impure it seems like love soda does a better
[06:13] it seems like love soda does a better job predicting who will
[06:15] job predicting who will and who will not love cool as ice
[06:19] and who will not love cool as ice but it would be nice if we could
[06:20] but it would be nice if we could quantify the differences between love's
[06:23] quantify the differences between love's popcorn
[06:23] popcorn and love soda the good news is that
[06:27] and love soda the good news is that there are several ways to quantify the
[06:29] there are several ways to quantify the impurity of the leaves
[06:32] impurity of the leaves one of the most popular methods is
[06:34] one of the most popular methods is called genie impurity
[06:36] called genie impurity but there are also fancy sounding
[06:38] but there are also fancy sounding methods like entropy
[06:39] methods like entropy and information gain however
[06:42] and information gain however numerically the methods are all quite
[06:45] numerically the methods are all quite similar
[06:46] similar so we will focus on genie impurity since
[06:49] so we will focus on genie impurity since not only is it very popular i think it
[06:52] not only is it very popular i think it is the most straightforward
[06:54] is the most straightforward so let's start by calculating the genie
[06:56] so let's start by calculating the genie impurity for love's popcorn
[06:59] impurity for love's popcorn to calculate the genie impurity for
[07:02] to calculate the genie impurity for love's popcorn
[07:03] love's popcorn we start by calculating the genie
[07:05] we start by calculating the genie impurity for the individual leaves
[07:08] impurity for the individual leaves the genie impurity for the leaf on the
[07:10] the genie impurity for the leaf on the left is
[07:12] left is 1 minus the probability of yes
[07:16] 1 minus the probability of yes squared minus the probability of
[07:19] squared minus the probability of no squared so we start out with one
[07:24] no squared so we start out with one then we subtract the squared probability
[07:26] then we subtract the squared probability of someone in this leaf
[07:28] of someone in this leaf loving cool as ice which is one
[07:32] loving cool as ice which is one the number of people in the leaf who
[07:33] the number of people in the leaf who loved cool as ice
[07:35] loved cool as ice divided by the total number of people in
[07:38] divided by the total number of people in the leaf four
[07:40] the leaf four and then the whole term is squared
[07:43] and then the whole term is squared lastly we subtract the squared
[07:45] lastly we subtract the squared probability of someone in this leaf
[07:47] probability of someone in this leaf not loving cool as ice which is three
[07:51] not loving cool as ice which is three the number of people in the leaf who did
[07:53] the number of people in the leaf who did not love cool as ice
[07:55] not love cool as ice divided by the total number of people in
[07:57] divided by the total number of people in the leaf
[07:59] the leaf squared and when we do the math
[08:02] squared and when we do the math we get 0.375
[08:05] we get 0.375 so let's put 0.375 under the leaf on the
[08:09] so let's put 0.375 under the leaf on the left
[08:09] left so we don't forget it now let's
[08:12] so we don't forget it now let's calculate the genie impurity for the
[08:14] calculate the genie impurity for the leaf on the right
[08:16] leaf on the right just like before we start out with one
[08:19] just like before we start out with one then we subtract the squared probability
[08:22] then we subtract the squared probability of someone in this leaf
[08:23] of someone in this leaf loving cool as ice and the squared
[08:26] loving cool as ice and the squared probability of someone in this leaf
[08:29] probability of someone in this leaf not a loving cool is ice
[08:32] not a loving cool is ice and when we do the math we get 0.444
[08:36] and when we do the math we get 0.444 now because the leaf on the left has
[08:39] now because the leaf on the left has four people in it
[08:40] four people in it and the leaf on the right only has three
[08:43] and the leaf on the right only has three people in it
[08:44] people in it the leaves do not represent the same
[08:46] the leaves do not represent the same number of people
[08:48] number of people thus the total genie impurity is the
[08:51] thus the total genie impurity is the weighted
[08:51] weighted average of the leaf impurities
[08:54] average of the leaf impurities we start by calculating the weight for
[08:57] we start by calculating the weight for the leaf on the left
[08:59] the leaf on the left the weight for the left leaf is the
[09:01] the weight for the left leaf is the total number of people in the leaf
[09:03] total number of people in the leaf four divided by the total number of
[09:06] four divided by the total number of people in both leaves
[09:08] people in both leaves seven then we multiply that weight
[09:12] seven then we multiply that weight by its associated genie impurity 0.375
[09:17] by its associated genie impurity 0.375 now we add the weighted impurity for the
[09:20] now we add the weighted impurity for the leaf on the right
[09:22] leaf on the right which is the total number of people in
[09:24] which is the total number of people in the leaf 3
[09:26] the leaf 3 divided by the total number of people in
[09:28] divided by the total number of people in both leaves
[09:29] both leaves 7 times the associated genie impurity
[09:34] 7 times the associated genie impurity 0.444 and when we do the math
[09:38] 0.444 and when we do the math we get 0.405
[09:41] we get 0.405 so the genie impurity for love's popcorn
[09:44] so the genie impurity for love's popcorn is 0.405
[09:47] is 0.405 likewise the genium purity for love soda
[09:51] likewise the genium purity for love soda is 0.214
[09:54] is 0.214 now we need to calculate the genie
[09:56] now we need to calculate the genie impurity for age
[09:58] impurity for age however because age contains numeric
[10:01] however because age contains numeric data
[10:02] data and not just yes no values calculating
[10:05] and not just yes no values calculating the genie impurity is a little more
[10:07] the genie impurity is a little more involved
[10:09] involved the first thing we do is sort the rows
[10:11] the first thing we do is sort the rows by age
[10:12] by age from lowest value to highest value
[10:15] from lowest value to highest value then we calculate the average age for
[10:17] then we calculate the average age for all adjacent people
[10:20] all adjacent people lastly we calculate the geniu impurity
[10:22] lastly we calculate the geniu impurity values for each
[10:24] values for each average age for example
[10:27] average age for example to calculate the gd impurity for the
[10:29] to calculate the gd impurity for the first value
[10:31] first value we put age less than 9.5 in the root
[10:35] we put age less than 9.5 in the root and because the only person with age
[10:37] and because the only person with age less than 9.5
[10:39] less than 9.5 does not love cool is ice
[10:42] does not love cool is ice we put a 0 under yes and a 1 under
[10:45] we put a 0 under yes and a 1 under no then everyone with age greater than
[10:49] no then everyone with age greater than or equal to 9.5
[10:51] or equal to 9.5 goes to the leaf on the right now we
[10:54] goes to the leaf on the right now we calculate the genie impurity for the
[10:56] calculate the genie impurity for the leaf on the left
[10:58] leaf on the left and get zero and this makes sense
[11:01] and get zero and this makes sense because
[11:02] because every single person in this leaf does
[11:04] every single person in this leaf does not love cool as ice
[11:06] not love cool as ice so there is no impurity
[11:10] so there is no impurity then we calculate the genie impurity for
[11:12] then we calculate the genie impurity for the leaf on the right
[11:14] the leaf on the right and get 0.5 now we calculate the
[11:18] and get 0.5 now we calculate the weighted average of the two impurities
[11:20] weighted average of the two impurities to get the total
[11:21] to get the total genie impurity and we get 0.429
[11:26] genie impurity and we get 0.429 likewise we calculate the genie
[11:28] likewise we calculate the genie impurities for all of the other
[11:30] impurities for all of the other candidate values
[11:33] candidate values these two candidate thresholds 15 and 44
[11:37] these two candidate thresholds 15 and 44 are tied for the lowest impurity 0.343
[11:42] are tied for the lowest impurity 0.343 so we can pick either one in this case
[11:44] so we can pick either one in this case we'll pick
[11:45] we'll pick 15. however remember that we are
[11:49] 15. however remember that we are comparing genie impurity values for
[11:51] comparing genie impurity values for age loves popcorn and love soda
[11:54] age loves popcorn and love soda to decide which features should be at
[11:56] to decide which features should be at the very top of the tree
[11:59] the very top of the tree earlier we calculated the genie impurity
[12:02] earlier we calculated the genie impurity values for love's popcorn
[12:04] values for love's popcorn and love soda and now we have the genie
[12:07] and love soda and now we have the genie impurity for age
[12:10] impurity for age and because love soda has the lowest
[12:13] and because love soda has the lowest genie impurity overall
[12:15] genie impurity overall we know that its leaves had the lowest
[12:17] we know that its leaves had the lowest impurity
[12:19] impurity so we put love soda at the top of the
[12:21] so we put love soda at the top of the tree
[12:22] tree bam now
[12:26] bam now the four people that love soda go to a
[12:28] the four people that love soda go to a node on the left
[12:30] node on the left and the people that do not love soda go
[12:33] and the people that do not love soda go to a node on the right
[12:36] to a node on the right now let's focus on the node on the left
[12:39] now let's focus on the node on the left all four people that love soda are in
[12:42] all four people that love soda are in this node
[12:44] this node three of these people love cool as ice
[12:48] three of these people love cool as ice and one does not so this
[12:51] and one does not so this node is impure so let's see if we can
[12:55] node is impure so let's see if we can reduce the impurity by splitting the
[12:57] reduce the impurity by splitting the people that love
[12:58] people that love soda based on love's popcorn or age
[13:03] soda based on love's popcorn or age we'll start by asking the four people
[13:05] we'll start by asking the four people that love soda
[13:06] that love soda if they also love popcorn
[13:09] if they also love popcorn because two of the four people that love
[13:11] because two of the four people that love soda
[13:12] soda also love popcorn they end up in the
[13:15] also love popcorn they end up in the leaf on the left
[13:18] leaf on the left the remaining two people that love soda
[13:20] the remaining two people that love soda but do not
[13:21] but do not love popcorn end up on the right
[13:24] love popcorn end up on the right and the total genie impurity for this
[13:26] and the total genie impurity for this split is 0.25
[13:30] split is 0.25 so let's put 0.25 here so we don't
[13:33] so let's put 0.25 here so we don't forget
[13:35] forget now we test different age thresholds
[13:37] now we test different age thresholds just like before
[13:39] just like before only this time we only consider the ages
[13:42] only this time we only consider the ages of people who love
[13:43] of people who love soda and age less than 12.5 gives us the
[13:48] soda and age less than 12.5 gives us the lowest impurity
[13:49] lowest impurity zero because both leaves have no
[13:52] zero because both leaves have no impurity at all
[13:55] impurity at all so let's put zero here now
[13:58] so let's put zero here now because zero is less than 0.25
[14:01] because zero is less than 0.25 we will use age less than 12.5 to split
[14:05] we will use age less than 12.5 to split this node into leaves
[14:07] this node into leaves note these are leaves because there is
[14:10] note these are leaves because there is no reason to continue splitting these
[14:12] no reason to continue splitting these people
[14:12] people into smaller groups likewise
[14:15] into smaller groups likewise this node consisting of the three people
[14:18] this node consisting of the three people who do not love
[14:19] who do not love soda is also a leaf because there is no
[14:22] soda is also a leaf because there is no reason to continue splitting these
[14:24] reason to continue splitting these people
[14:25] people into smaller groups now there is just
[14:29] into smaller groups now there is just one last thing we need to do before we
[14:31] one last thing we need to do before we are done building this tree
[14:34] are done building this tree we need to assign output values for each
[14:36] we need to assign output values for each leaf
[14:38] leaf generally speaking the output of a leaf
[14:41] generally speaking the output of a leaf is whatever category that has the most
[14:43] is whatever category that has the most values
[14:45] values in other words because the majority of
[14:47] in other words because the majority of the people in these leaves
[14:48] the people in these leaves do not love cool as ice
[14:51] do not love cool as ice the output values are does not love
[14:55] the output values are does not love cool as ice and because the majority of
[14:58] cool as ice and because the majority of the people in this leaf
[15:00] the people in this leaf love cool as ice the output value is
[15:03] love cool as ice the output value is love's cool as ice hooray
[15:07] love's cool as ice hooray we finished building a tree from this
[15:09] we finished building a tree from this data
[15:11] data double bam now if someone new comes
[15:15] double bam now if someone new comes along
[15:16] along and we want to predict if they will love
[15:18] and we want to predict if they will love cool as ice
[15:19] cool as ice then we run the data down our tree and
[15:22] then we run the data down our tree and because they love
[15:23] because they love soda they go to the left and because
[15:26] soda they go to the left and because they are 15
[15:28] they are 15 so age less than 12.5 is false
[15:31] so age less than 12.5 is false they end up in this leaf and we predict
[15:34] they end up in this leaf and we predict that they will love cool as ice
[15:37] that they will love cool as ice triple bam okay
[15:41] triple bam okay now that we understand the main ideas of
[15:43] now that we understand the main ideas of how to build and use classification
[15:45] how to build and use classification trees
[15:46] trees let's discuss one technical detail
[15:49] let's discuss one technical detail remember when we built this tree only
[15:52] remember when we built this tree only one person in the original
[15:54] one person in the original data set made it to this leaf
[15:57] data set made it to this leaf because so few people made it to this
[15:59] because so few people made it to this leaf it's hard to have confidence that
[16:01] leaf it's hard to have confidence that it will do a great job making
[16:03] it will do a great job making predictions with future data
[16:05] predictions with future data and it is possible that we have overfit
[16:08] and it is possible that we have overfit the data
[16:09] the data note if the term overfit is new to you
[16:13] note if the term overfit is new to you don't don't
[16:16] instead check out the stack quest on bias and variance in machine learning
[16:21] bias and variance in machine learning regardless in practice there are two
[16:24] regardless in practice there are two main ways to deal with this problem
[16:27] main ways to deal with this problem one method is called pruning and there's
[16:29] one method is called pruning and there's a whole stack quest dedicated to it so
[16:31] a whole stack quest dedicated to it so check it out
[16:33] check it out alternatively we can put limits on how
[16:36] alternatively we can put limits on how trees grow
[16:37] trees grow for example by requiring three or more
[16:40] for example by requiring three or more people per leaf
[16:42] people per leaf now we end up with an impure leaf but
[16:45] now we end up with an impure leaf but also a better sense of the accuracy of
[16:47] also a better sense of the accuracy of our prediction
[16:48] our prediction because we know that only 75 percent of
[16:50] because we know that only 75 percent of the people
[16:51] the people in the leaf love to cool as ice
[16:55] in the leaf love to cool as ice note even when a leaf is impure we still
[16:58] note even when a leaf is impure we still need an
[16:58] need an output value to make a classification
[17:01] output value to make a classification and since most of the people in this
[17:03] and since most of the people in this leaf
[17:04] leaf love cool as ice that will be the output
[17:07] love cool as ice that will be the output value
[17:08] value also note when we build a tree we don't
[17:11] also note when we build a tree we don't know in advance if it is better to
[17:13] know in advance if it is better to require three people per leaf
[17:15] require three people per leaf or some other number so we test
[17:18] or some other number so we test different values with something called
[17:19] different values with something called cross validation
[17:21] cross validation and pick the one that works best and if
[17:23] and pick the one that works best and if you don't know what cross validation is
[17:26] you don't know what cross validation is check out the quest bam now it's time
[17:29] check out the quest bam now it's time for some
[17:30] for some shameless self-promotion if you want to
[17:33] shameless self-promotion if you want to review statistics and machine learning
[17:35] review statistics and machine learning offline
[17:36] offline check out the statquest study guides at
[17:38] check out the statquest study guides at statquest.org
[17:40] statquest.org there's something for everyone hooray
[17:43] there's something for everyone hooray we've made it to the end of another
[17:45] we've made it to the end of another exciting stat quest
[17:46] exciting stat quest if you like this stat quest and want to
[17:48] if you like this stat quest and want to see more please subscribe
[17:50] see more please subscribe and if you want to support statquest
[17:52] and if you want to support statquest consider contributing to my patreon
[17:54] consider contributing to my patreon campaign
[17:55] campaign becoming a channel member buying one or
[17:58] becoming a channel member buying one or two of my original songs or a t-shirt or
[18:00] two of my original songs or a t-shirt or a hoodie or just donate
[18:02] a hoodie or just donate the links are in the description below
[18:04] the links are in the description below alright until next time
[18:06] alright until next time quest on

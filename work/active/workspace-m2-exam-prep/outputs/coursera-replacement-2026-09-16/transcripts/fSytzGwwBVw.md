---
video_id: fSytzGwwBVw
url: https://www.youtube.com/watch?v=fSytzGwwBVw
title: Machine Learning Fundamentals: Cross Validation
channel: StatQuest with Josh Starmer
duration: 6:04
language: en
unit: L11
status: OK
---

[00:00] StatQuest
[00:01] Check it out
[00:03] talking about
[00:05] Machine-learning. Yeah StatQuest
[00:08] Check it out
[00:09] Talking about cross-validation
[00:12] StatQuest
[00:15] Hello, I'm Josh stormer and welcome to StatQuest today we're going to talk about cross validation and it's gonna be clearly explained
[00:25] Okay, let's start with some data
[00:28] We want to use the variables chest pain good blood circulation
[00:33] Etc
[00:34] To predict if someone has heart disease
[00:37] Then when a new patient shows up
[00:40] we can measure these variables and
[00:43] Predict if they have heart disease or not
[00:47] However, first we have to decide which machine learning method would be best
[00:53] we could use logistic regression or
[00:56] K nearest neighbors
[00:59] Or support vector machines and
[01:03] Many more machine learning methods. How do we decide which one to use?
[01:09] Cross-validation allows us to compare different machine learning methods and get a sense of how well they will work in practice
[01:19] Imagine that this blue column represented all of the data that we have collected about people with and without heart disease
[01:27] We need to do two things with this data
[01:30] One we need to estimate the parameters for the machine learning methods in
[01:36] In other words to use logistic regression we have to use some of the data to estimate the shape of this curve
[01:44] in machine learning lingo
[01:47] Estimating parameters is called training the algorithm
[01:51] The second thing we need to do with this data is evaluate how well the machine learning methods work in?
[01:58] Other words we need to find out if this curve will do a good job categorizing new data in
[02:06] In machine learning lingo
[02:09] Evaluating a method is called testing the algorithm
[02:13] Thus using machine learning lingo we need the data to
[02:18] one train the machine learning methods and
[02:22] to test the machine learning methods a
[02:27] A terrible approach would be to use all the data to estimate the parameters ie to train the algorithm
[02:35] Because then we wouldn't have any data left to test the method
[02:40] Reusing the same data for both training and
[02:43] Testing is a bad idea because we need to know how the method will work on data. It wasn't trained on a
[02:52] Slightly better idea would be to use the first seventy-five percent of the data for training and the last 25% of the data for testing
[03:02] We could then compare methods by seeing how well each one categorized the test data
[03:09] But how do we know that using the first?
[03:11] Seventy-five percent of the data for training in the last 25% of the data for testing is the best way to divide up the data
[03:21] What if we use the first 25% of the data for testing
[03:26] Or what about one of these middle blocks?
[03:29] Rather than worry too much about which block would be best for testing cross-validation uses them all one at a time and summarizes the results at the end
[03:41] For example cross-validation would start by using the first three blocks to train the method and
[03:49] then use the last block to test the method and
[03:53] Then it keeps track of how well the method did with the test data
[03:58] then it uses this combination of blocks to train the method and
[04:03] this block is used for testing and
[04:07] Then it keeps track of how well the method did with the test data, etc
[04:12] Etc, etc
[04:16] in the end every block of data is used for testing and we can compare methods by seeing how well they performed in
[04:25] This case since the support vector machine did the best job classifying the test data sets. We'll use it
[04:33] BAM!!!
[04:36] Note: in this example, we divided the data into 4 blocks. This is called four-fold cross validation
[04:45] However, the number of blocks is arbitrary
[04:49] In an extreme case we could call each individual patient (or sample) a block
[04:56] This is called "Leave One Out Cross Validation"
[04:59] Each sample is tested individually
[05:03] That said in practice it is very common to divide the data into ten blocks. This is called 10-fold cross-validation
[05:14] Double BAM!!!
[05:16] One last note before we're done
[05:20] Say like we wanted to use a method that involved a tuning parameter a parameter that isn't estimated but is just sort of guessed
[05:28] For example Ridge regression has a tuning parameter
[05:33] Then we could use 10-fold cross validation
[05:36] to help find the best value for that tuning parameter
[05:40] Tiny Bam!
[05:42] Hooray we've made it to the end of another exciting StatQuest if you like this StatQuest and want to see more please subscribe
[05:50] And if you want to support StatQuest well
[05:54] Please click the like button down below and consider buying one of my original songs
[05:59] Alright until next time quest on

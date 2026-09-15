---
video_id: J4Wdy0Wc_xQ
url: https://www.youtube.com/watch?v=J4Wdy0Wc_xQ
title: StatQuest: Random Forests Part 1 - Building, Using and Evaluating
channel: StatQuest with Josh Starmer
duration: 9:54
language: en
unit: L12
status: OK
---

[00:00] Wandering around a random forest. I won't get lost because of stat quest
[00:10] Hello, I'm Josh Dharma and welcome to stat quest today
[00:14] We're gonna be starting part one of a series on random forests, and we're going to talk about building and evaluating random forests
[00:22] Note random forests are built from decision trees. So if you don't already know about those check out my stat quest and beef up
[00:31] Decision trees are easy to build easy to use and easy to interpret
[00:37] But in practice they are not that awesome
[00:41] to quote from the elements of statistical learning
[00:44] Aka the Bible of machine learning
[00:47] Trees have one aspect that prevents them from being the ideal tool for predictive learning
[00:52] Namely in accuracy. In other words, they work great with the data used to create them
[00:59] But they are not flexible when it comes to classifying new samples
[01:04] The good news is that random forests combine the simplicity of decision trees with flexibility
[01:10] Resulting in a vast improvement in accuracy
[01:14] So let's make a random forest
[01:17] step 1 create a bootstrap data set
[01:21] imagine that these 4 samples are the entire data set that we are going to build a tree from I
[01:27] Know it's crazy small, but just pretend for now
[01:31] To create a bootstrap data set that is the same size as the original. We just randomly select samples from the original data set
[01:39] The important detail is that we're allowed to pick the same sample more than once
[01:45] This is the first sample that we randomly select
[01:49] So it's the first sample in our bootstrap data set
[01:53] This is the second randomly selected sample from the original data set
[01:58] So it's the second sample in our bootstrap data set
[02:02] Here's the third randomly selected sample
[02:05] So here it is in the bootstrap data set
[02:09] Lastly here's the fourth randomly selected sample note. It's the same as the third and
[02:16] Here it is
[02:18] BAM we've created a bootstrap data set
[02:24] Step2 for creating a random forest is to create a decision tree using the bootstrap dataset
[02:30] But only use a random subset of variables or columns at each step in
[02:36] This example, we will only consider two variables or columns at each step
[02:42] Note, we'll talk more about how to determine the optimal number of variables to consider later
[02:49] Thus instead of considering all four variables to figure out how to split the root node
[02:55] We randomly select two in
[02:59] This case we randomly selected good blood circulation and blocked arteries as candidates for the root node
[03:07] Just for the sake of the example assume that good blood circulation. Did the best job separating the samples?
[03:15] Since we used a good blood circulation, I'm going to gray it out so that we focus on the remaining variables
[03:23] Now we need to figure out how to split samples at this node
[03:28] just like for the route we randomly select two variables as candidates instead of all three remaining columns and
[03:36] We just build the tree as usual, but only considering a random subset of variables at each step
[03:44] double bound
[03:46] we built a tree one using a bootstrap data set and
[03:50] Two only considering a random subset of variables at each step
[03:56] Here's the tree we just made
[04:00] Now go back to step one and repeat
[04:03] Make a new bootstrap data set and build a tree considering a subset of variables at each step
[04:10] Ideally you do this hundreds of times, but we only have space to show six, but you get the idea
[04:18] Using a bootstrap sample and considering only a subset of variables at each step results in a wide variety of trees
[04:27] The variety is what makes random forests more effective than individual decision trees
[04:34] Sweet now that we've created a random forest. How do we use it?
[04:40] Well first we get a new patient
[04:43] We've got all the measurements and now we want to know if they have heart disease or not
[04:51] So we take the data and run it down the first tree that we made
[04:56] Booboo, dooba, dooba, dooba dooba, dooba. Do the first tree says yes, the patient has heart disease and
[05:04] We keep track of that here
[05:08] now we run the data down the second tree that we made the second tree also says yes and
[05:16] We keep track of that here. And then we repeat for all the trees we made
[05:24] After running the data down all of the trees in the random forest. We see which option received more votes in
[05:31] This case yes received the most votes so we will conclude that this patient has heart disease
[05:39] BAM
[05:40] Oh
[05:42] No terminology alert
[05:46] Bootstrapping the data plus using the aggregate to make a decision is called bagging
[05:53] Okay, now we've seen how to create and use a random forest
[05:59] How do we know if it's any good
[06:03] Remember when we created the bootstrapped data set
[06:08] We allow duplicates in trees in the bootstrapped data set as
[06:13] A result. This entry was not included in the bootstrap data set
[06:19] Typically about one third of the original data does not end up in the bootstrap data set
[06:26] Here's the entry that didn't end up in the bootstrapped dataset
[06:31] If the original dataset were larger, we'd have more than just one entry over here
[06:38] This is called the out-of-bag data set
[06:42] If it were up to me
[06:44] I would have named it thee out of boot data set since it's the entries that didn't make it into the bootstrap dataset
[06:51] Unfortunately, it's not up to me
[06:53] Since the out-of-bag data was not used to create this tree
[06:58] We can run it through and see if it correctly classifies the sample as no heart disease
[07:04] In this case the tree correctly labels the out of bag sample. No
[07:11] Then we run this out of bag sample through all of the other trees that were built without it
[07:17] This tree incorrectly labeled the out of bag sample. Yes
[07:23] These trees correctly labeled the out of bag sample know
[07:28] Since the label with the most votes wins is the label that we assign this out of bag sample in
[07:35] This case the out of bag sample is correctly labeled by the random forest
[07:41] We then do the same thing for all of the other out of bag samples for all of the trees
[07:47] This out of bag sample was also correctly labeled
[07:53] This out of bag sample was incorrectly labeled
[07:58] Etc etc, etc
[08:03] Ultimately we can measure how accurate our random forest is by the proportion of out-of-bag samples that were correctly
[08:10] classified by the random forest
[08:13] The proportion of out-of-bag samples that were incorrectly classified is the out of bag error
[08:21] Okay, we now know how to one build a random forest to use a random forest and
[08:29] three estimate the accuracy of a random forest
[08:34] However now that we know how to do this we can talk a little more about how to do this
[08:42] Remember when we built our first tree and we only use two variables
[08:46] columns of data to make a decision at each step
[08:51] Now we can compare the out-of-bag error for a random forest built using only two variables per step
[08:58] to a random forest built using three variables per step and
[09:03] We test a bunch of different settings and choose the most accurate random forest
[09:09] In other words one we build a random forest and then two we estimate the accuracy of a random forest
[09:18] then we change the number of variables used per step and
[09:22] We do this a bunch of times and then choose the one that is the most accurate
[09:28] Typically we start by using the square of the number of variables and then try a few settings above and below that value
[09:38] Triple bail
[09:40] Hooray
[09:41] We've made it to the end of another exciting static quest tune in next week
[09:45] And we'll talk about how to deal with missing data and how to cluster the samples. All right, and tell them quest are armed

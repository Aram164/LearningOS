---
video_id: udyAvvaMjfM
url: https://www.youtube.com/watch?v=udyAvvaMjfM
title: Fisher's Exact Test and the Hypergeometric Distribution
channel: StatQuest with Josh Starmer
duration: 5:15
language: en
unit: L05
status: OK
---

[00:00] Hello and welcome to a stat quickie.
[00:03] Hello and welcome to a stat quickie. Today we're going to talk about Fisher's
[00:05] Today we're going to talk about Fisher's exact test and enrichment analysis.
[00:08] exact test and enrichment analysis. But first, let's eat some M&amp;M's.
[00:12] But first, let's eat some M&amp;M's. I want to share some with my friends, so
[00:15] I want to share some with my friends, so I just take one handful and get seven
[00:18] I just take one handful and get seven blue and one red.
[00:21] blue and one red. What does this say about the
[00:23] What does this say about the distribution of colors in the bag?
[00:26] distribution of colors in the bag? Do I have more blues than normal?
[00:29] Do I have more blues than normal? Lastly, can I calculate a P value from
[00:32] Lastly, can I calculate a P value from this delicious sample?
[00:35] this delicious sample? This bag is supposed to have two
[00:36] This bag is supposed to have two servings and I think a serving of M&amp;M's
[00:39] servings and I think a serving of M&amp;M's is 20 M&amp;M's. So there must be 40 M&amp;M's
[00:42] is 20 M&amp;M's. So there must be 40 M&amp;M's in the bag.
[00:44] in the bag. I looked up the proportions of the
[00:46] I looked up the proportions of the different colors of M&amp;M's on the
[00:47] different colors of M&amp;M's on the internet and this is what I found.
[00:51] internet and this is what I found. So on the right, we have a histogram of
[00:54] So on the right, we have a histogram of an idealized bag of M&amp;M's.
[00:58] an idealized bag of M&amp;M's. I'm going to use the histogram of the
[01:00] I'm going to use the histogram of the ideal bag of M&amp;M's
[01:02] ideal bag of M&amp;M's based on the proportions I got off the
[01:03] based on the proportions I got off the internet
[01:05] internet and my sample, my handful of M&amp;M's, to
[01:08] and my sample, my handful of M&amp;M's, to determine if my bag is special.
[01:11] determine if my bag is special. In this example, I don't care about the
[01:14] In this example, I don't care about the order of how the M&amp;M's fell into my
[01:16] order of how the M&amp;M's fell into my hand. So let's consider every possible
[01:19] hand. So let's consider every possible ordering of seven blue and one red as
[01:23] ordering of seven blue and one red as legit.
[01:25] legit. Let's start by calculating the
[01:27] Let's start by calculating the probability of getting seven blue M&amp;M's
[01:30] probability of getting seven blue M&amp;M's followed by a single red M&amp;M.
[01:33] followed by a single red M&amp;M. The probability that the first M&amp;M is
[01:36] The probability that the first M&amp;M is blue equals 8 divided by 40.
[01:40] blue equals 8 divided by 40. 8 because there are eight blue M&amp;M's
[01:44] 8 because there are eight blue M&amp;M's divided by 40 because there are 40 M&amp;M's
[01:47] divided by 40 because there are 40 M&amp;M's total.
[01:48] total. Now that I've got one M&amp;M in my hand,
[01:51] Now that I've got one M&amp;M in my hand, there are only seven blue M&amp;M's left in
[01:53] there are only seven blue M&amp;M's left in the bag.
[01:55] the bag. The probability that the second M&amp;M is
[01:57] The probability that the second M&amp;M is blue equals 7 / 39.
[02:01] blue equals 7 / 39. Seven because there are now only seven
[02:03] Seven because there are now only seven blue M&amp;M's in the bag
[02:06] blue M&amp;M's in the bag / 39 because there are only 39 M&amp;M's.
[02:11] / 39 because there are only 39 M&amp;M's. Now there are only six blue M&amp;M's left
[02:13] Now there are only six blue M&amp;M's left in the bag.
[02:15] in the bag. The probability of getting a third blue
[02:17] The probability of getting a third blue M&amp;M is 6 / 38
[02:20] M&amp;M is 6 / 38 leaving five blue M&amp;M's left in the bag.
[02:24] leaving five blue M&amp;M's left in the bag. And by now you've probably grasped the
[02:26] And by now you've probably grasped the pattern for how we determine the
[02:28] pattern for how we determine the probabilities for getting a sequence of
[02:31] probabilities for getting a sequence of blue M&amp;M's.
[02:33] blue M&amp;M's. Once we have calculated the
[02:35] Once we have calculated the probabilities for getting seven blue
[02:37] probabilities for getting seven blue M&amp;M's in our hand we can now calculate
[02:39] M&amp;M's in our hand we can now calculate the probability of getting one red M&amp;M.
[02:43] the probability of getting one red M&amp;M. That's just 5 / 33.
[02:46] That's just 5 / 33. Five because there are five red M&amp;M's
[02:50] Five because there are five red M&amp;M's / 33 because there are 33 M&amp;M's left in
[02:54] / 33 because there are 33 M&amp;M's left in the bag at this point.
[02:57] the bag at this point. Now just multiply all those
[02:59] Now just multiply all those probabilities together to get the
[03:01] probabilities together to get the probability of getting seven blues
[03:03] probability of getting seven blues followed by one red.
[03:06] followed by one red. And that just equals a really small
[03:08] And that just equals a really small number.
[03:10] number. That's rare
[03:12] That's rare but remember we don't care about order.
[03:15] but remember we don't care about order. There's more work to do to get the
[03:17] There's more work to do to get the probability of seven blues and one red
[03:20] probability of seven blues and one red in any order.
[03:23] in any order. To calculate the probability of getting
[03:25] To calculate the probability of getting seven blues and one red we have to add
[03:28] seven blues and one red we have to add together the probabilities of each
[03:30] together the probabilities of each possible ordering.
[03:31] possible ordering. The good news is that the process of
[03:33] The good news is that the process of calculating the probabilities is the
[03:35] calculating the probabilities is the same as what we just did.
[03:38] same as what we just did. Good thing we have computers cuz they'll
[03:40] Good thing we have computers cuz they'll do the work for us.
[03:42] do the work for us. Anyways, the probability is still really
[03:44] Anyways, the probability is still really small.
[03:47] small. Now what's the P value? If you'll
[03:48] Now what's the P value? If you'll remember from the P value stat quest
[03:51] remember from the P value stat quest sometimes you can have very small
[03:52] sometimes you can have very small probabilities, but really large P
[03:55] probabilities, but really large P values.
[03:56] values. And remember,
[03:58] And remember, a P value is the sum of the
[04:00] a P value is the sum of the probabilities of all things equally rare
[04:03] probabilities of all things equally rare or rarer.
[04:05] or rarer. This is all covered in the StatQuest on
[04:07] This is all covered in the StatQuest on P values.
[04:09] P values. So that includes adding the probability
[04:12] So that includes adding the probability of getting eight blues in a row
[04:15] of getting eight blues in a row or seven oranges and one blue
[04:17] or seven oranges and one blue because that's equally rare.
[04:20] because that's equally rare. And actually, there are a lot of
[04:22] And actually, there are a lot of different ways you can come up with
[04:23] different ways you can come up with things that are equally rare or rarer.
[04:26] things that are equally rare or rarer. Too many to put on this Stat quickie. So
[04:28] Too many to put on this Stat quickie. So we're just going to skip to the chase.
[04:31] we're just going to skip to the chase. Again, good thing we have computers.
[04:34] Again, good thing we have computers. The P value ends up being 0.01.
[04:38] The P value ends up being 0.01. So my bag is special. Hooray!
[04:42] So my bag is special. Hooray! We just performed Fisher's exact test on
[04:44] We just performed Fisher's exact test on the M&amp;M's.
[04:46] the M&amp;M's. Enrichment for other things like does
[04:49] Enrichment for other things like does this list of genes have more involved in
[04:51] this list of genes have more involved in metabolism than normal? Is done the
[04:53] metabolism than normal? Is done the exact same way.
[04:56] exact same way. And for any of you StatQuesters that use
[04:58] And for any of you StatQuesters that use R, a programming language for doing
[05:01] R, a programming language for doing statistics,
[05:02] statistics, I've provided the R code for doing the
[05:04] I've provided the R code for doing the Fisher's exact test that we performed on
[05:07] Fisher's exact test that we performed on the M&amp;M's in the description below.
[05:10] the M&amp;M's in the description below. Hooray! Tune in next week for another
[05:13] Hooray! Tune in next week for another Stat quickie.

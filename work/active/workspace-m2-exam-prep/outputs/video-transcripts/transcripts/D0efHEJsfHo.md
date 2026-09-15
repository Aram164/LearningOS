---
video_id: D0efHEJsfHo
url: https://www.youtube.com/watch?v=D0efHEJsfHo
title: How to Prune Regression Trees, Clearly Explained!!!
channel: StatQuest with Josh Starmer
duration: 16:15
language: en
unit: L12
status: OK
---

[00:00] Smellystat, Smellystat,
[00:03] Smellystat, how are they training you? I hope
[00:06] how are they training you? I hope they're using StatQuest.
[00:09] they're using StatQuest. Hello, I'm Josh Starmer and welcome to
[00:11] Hello, I'm Josh Starmer and welcome to StatQuest. Today, we're going to talk
[00:14] StatQuest. Today, we're going to talk about how to prune regression trees.
[00:17] about how to prune regression trees. There are several methods for pruning
[00:19] There are several methods for pruning regression trees. The one we'll talk
[00:22] regression trees. The one we'll talk about in this quest is called
[00:23] about in this quest is called cost-complexity pruning, aka weakest
[00:27] cost-complexity pruning, aka weakest link pruning.
[00:29] link pruning. We'll start by giving a general overview
[00:32] We'll start by giving a general overview of how cost-complexity pruning works,
[00:35] of how cost-complexity pruning works, and then we'll describe how it's used to
[00:36] and then we'll describe how it's used to build regression trees.
[00:39] build regression trees. Note, this StatQuest assumes that you
[00:42] Note, this StatQuest assumes that you are already familiar with regression
[00:44] are already familiar with regression trees. If not, check out the quest. The
[00:47] trees. If not, check out the quest. The link is in the description below.
[00:50] link is in the description below. Also note, this StatQuest assumes that
[00:52] Also note, this StatQuest assumes that you are already familiar with
[00:54] you are already familiar with cross-validation.
[00:56] cross-validation. If not, check out the quest.
[00:59] If not, check out the quest. In the StatQuest on regression trees, we
[01:02] In the StatQuest on regression trees, we had this data.
[01:03] had this data. Given different drug dosages on the
[01:06] Given different drug dosages on the x-axis,
[01:08] x-axis, we measured the drug effectiveness on
[01:10] we measured the drug effectiveness on the y-axis.
[01:13] the y-axis. When the drug dosage was too low
[01:16] When the drug dosage was too low or too high,
[01:18] or too high, the drug was not effective.
[01:21] the drug was not effective. Medium dosages were very effective.
[01:25] Medium dosages were very effective. And moderately high dosages were
[01:27] And moderately high dosages were moderately effective.
[01:30] moderately effective. We then fit a regression tree to the
[01:32] We then fit a regression tree to the data.
[01:33] data. And each leaf corresponded to the
[01:36] And each leaf corresponded to the average drug effectiveness from a
[01:38] average drug effectiveness from a different cluster of observations.
[01:42] different cluster of observations. This tree does a pretty good job
[01:44] This tree does a pretty good job reflecting the training data.
[01:47] reflecting the training data. Because each leaf represents a value
[01:49] Because each leaf represents a value that is close to the data.
[01:52] that is close to the data. However, what if these red circles were
[01:55] However, what if these red circles were testing data.
[01:57] testing data. These three observations
[02:00] These three observations are pretty close to the predicted
[02:02] are pretty close to the predicted values.
[02:03] values. So, their residuals, the difference
[02:05] So, their residuals, the difference between the observed and predicted
[02:07] between the observed and predicted values, are not very large.
[02:11] values, are not very large. Similarly, the residuals for these
[02:13] Similarly, the residuals for these observations in the testing data are
[02:16] observations in the testing data are relatively small.
[02:18] relatively small. However, the residuals for these
[02:20] However, the residuals for these observations are larger than before.
[02:24] observations are larger than before. And the residuals for these observations
[02:26] And the residuals for these observations are much larger.
[02:29] are much larger. These four observations from the
[02:31] These four observations from the training data with 100% drug
[02:33] training data with 100% drug effectiveness now look a little bit like
[02:36] effectiveness now look a little bit like outliers.
[02:38] outliers. And that means that we overfit the
[02:40] And that means that we overfit the regression tree to the training data.
[02:44] regression tree to the training data. One way to prevent overfitting a
[02:46] One way to prevent overfitting a regression tree to the training data is
[02:49] regression tree to the training data is to remove some of the leaves
[02:51] to remove some of the leaves and replace the split with a leaf that
[02:54] and replace the split with a leaf that is the average of a larger number of
[02:56] is the average of a larger number of observations.
[02:59] observations. Now, all of the observations between
[03:01] Now, all of the observations between 14.5
[03:03] 14.5 and 29 go to the leaf on the far right.
[03:08] and 29 go to the leaf on the far right. The large residuals tell us that the new
[03:10] The large residuals tell us that the new tree doesn't fit the training data as
[03:12] tree doesn't fit the training data as well as before.
[03:14] well as before. But, the new subtree does a much better
[03:17] But, the new subtree does a much better job with the testing data.
[03:20] job with the testing data. Thus, the main idea behind pruning a
[03:23] Thus, the main idea behind pruning a regression tree is to prevent
[03:25] regression tree is to prevent overfitting the training data
[03:28] overfitting the training data so that the tree will do a better job
[03:30] so that the tree will do a better job with the testing data.
[03:33] with the testing data. Bam!
[03:36] Bam! Note, if we wanted to prune the tree
[03:38] Note, if we wanted to prune the tree more, we could remove these two leaves
[03:41] more, we could remove these two leaves and replace the split with a leaf that
[03:44] and replace the split with a leaf that is the average of a larger number of
[03:46] is the average of a larger number of observations.
[03:48] observations. And we could then remove these two
[03:50] And we could then remove these two leaves
[03:51] leaves and replace the split with a leaf that
[03:54] and replace the split with a leaf that is the average of all of the
[03:56] is the average of all of the observations.
[03:58] observations. So, the question is, how do we decide
[04:01] So, the question is, how do we decide which tree to use?
[04:04] which tree to use? In this StatQuest, we will answer that
[04:06] In this StatQuest, we will answer that question with cost complexity pruning.
[04:11] question with cost complexity pruning. The first step in cost complexity
[04:13] The first step in cost complexity pruning is to calculate the sum of the
[04:15] pruning is to calculate the sum of the squared residuals for each tree.
[04:19] squared residuals for each tree. In this example, we'll start with the
[04:21] In this example, we'll start with the original full-sized tree.
[04:24] original full-sized tree. Here is the original full-sized tree.
[04:29] Here is the original full-sized tree. The sum of the squared residuals for the
[04:31] The sum of the squared residuals for the observations with dosages less than 14.5
[04:35] observations with dosages less than 14.5 is
[04:39] 320.8.
[04:43] So, we'll save that sum of squared residuals underneath the corresponding
[04:47] residuals underneath the corresponding leaf.
[04:49] leaf. The sum of squared residuals for
[04:51] The sum of squared residuals for observations with dosages greater than
[04:54] observations with dosages greater than or equal to 29
[04:56] or equal to 29 is 75.
[04:59] is 75. The sum of squared residuals for
[05:01] The sum of squared residuals for observations with dosages greater than
[05:03] observations with dosages greater than or equal to 23 and less than 29
[05:07] or equal to 23 and less than 29 is 148.8.
[05:11] And the sum of squared residuals for observations with dosages greater than
[05:16] observations with dosages greater than or equal to 14.5
[05:18] or equal to 14.5 and less than 23.5
[05:21] and less than 23.5 is zero.
[05:23] is zero. Thus, the total sum of squared residuals
[05:26] Thus, the total sum of squared residuals for the whole tree is 320 + 75 + 148.8
[05:33] for the whole tree is 320 + 75 + 148.8 + 0 = 543.8.
[05:39] So, let's put SSR = 543.8
[05:43] So, let's put SSR = 543.8 on top of the original full-sized tree.
[05:47] on top of the original full-sized tree. Now, let's calculate the sum of squared
[05:49] Now, let's calculate the sum of squared residuals for the subtree with one fewer
[05:52] residuals for the subtree with one fewer leaf.
[05:54] leaf. Going back to the data,
[05:56] Going back to the data, the sum of squared residuals for when
[05:58] the sum of squared residuals for when dosage is less than 14.5
[06:01] dosage is less than 14.5 is the same as before.
[06:03] is the same as before. And it's the same for when dosage is
[06:06] And it's the same for when dosage is greater than or equal to 29.
[06:09] greater than or equal to 29. But we have to calculate a new sum of
[06:11] But we have to calculate a new sum of squared residuals for when the dosage is
[06:14] squared residuals for when the dosage is between 14.5
[06:16] between 14.5 and 29.
[06:18] and 29. Thus, the total sum of squared residuals
[06:21] Thus, the total sum of squared residuals for this tree is 320 + 75 + 5,099.8,
[06:29] for this tree is 320 + 75 + 5,099.8, which equals 5,494.8.
[06:34] So, let's put SSR = 5,494.8
[06:40] on top of the subtree with three leaves.
[06:44] on top of the subtree with three leaves. Similarly, the sum of squared residuals
[06:46] Similarly, the sum of squared residuals for the subtree with two leaves
[06:49] for the subtree with two leaves is 19,243.7.
[06:54] So, we put SSR = 19,243.7
[07:00] on top of the subtree with two leaves.
[07:04] on top of the subtree with two leaves. Lastly, the sum of squared residuals for
[07:06] Lastly, the sum of squared residuals for the subtree with only one leaf
[07:09] the subtree with only one leaf is 28,897.2.
[07:14] So, let's put SSR = 28,897.2
[07:20] on top of the subtree with one leaf.
[07:24] on top of the subtree with one leaf. Note, the sum of squared residuals is
[07:27] Note, the sum of squared residuals is relatively small for the original
[07:29] relatively small for the original full-sized tree,
[07:31] full-sized tree, but each time we remove a leaf, the sum
[07:34] but each time we remove a leaf, the sum of squared residuals gets larger and
[07:36] of squared residuals gets larger and larger.
[07:38] larger. However, we knew that was going to
[07:40] However, we knew that was going to happen because the whole idea was for
[07:43] happen because the whole idea was for the pruned trees to not fit the training
[07:46] the pruned trees to not fit the training data as well as the full-sized tree.
[07:50] data as well as the full-sized tree. So, how do we compare these trees?
[07:54] So, how do we compare these trees? Weakest link pruning works by
[07:56] Weakest link pruning works by calculating a tree score
[07:59] calculating a tree score that is based on the sum of squared
[08:01] that is based on the sum of squared residuals for the tree or subtree
[08:05] residuals for the tree or subtree and a tree complexity penalty that is a
[08:08] and a tree complexity penalty that is a function of the number of leaves or
[08:10] function of the number of leaves or terminal nodes in the tree or subtree.
[08:15] terminal nodes in the tree or subtree. The tree complexity penalty compensates
[08:18] The tree complexity penalty compensates for the difference in the number of
[08:20] for the difference in the number of leaves.
[08:22] leaves. Note, alpha is a tuning parameter that
[08:25] Note, alpha is a tuning parameter that we find using cross-validation
[08:27] we find using cross-validation and we'll talk more about it in a bit.
[08:31] and we'll talk more about it in a bit. For now, let's let alpha equal 10,000.
[08:35] For now, let's let alpha equal 10,000. Now, let's calculate the tree score for
[08:38] Now, let's calculate the tree score for each tree.
[08:40] each tree. The tree score for the original
[08:42] The tree score for the original full-sized tree is
[08:45] full-sized tree is the total SSR for the tree, which is
[08:48] the total SSR for the tree, which is 543.8,
[08:51] 543.8, plus 10,000 * T, the total number of
[08:54] plus 10,000 * T, the total number of leaves, which is four.
[08:57] leaves, which is four. So, the tree score for the original
[08:59] So, the tree score for the original full-sized tree is 40,543.8.
[09:06] Now, let's save the tree score below the tree
[09:10] tree and calculate the tree score for the
[09:12] and calculate the tree score for the subtree with one fewer leaf.
[09:15] subtree with one fewer leaf. The sum of squared residuals for this
[09:17] The sum of squared residuals for this subtree is 5,494.8.
[09:23] And since there are three leaves, T
[09:26] And since there are three leaves, T equals three,
[09:28] equals three, and the total tree score equals
[09:30] and the total tree score equals 35,494.8.
[09:35] The tree score for the subtree with two leaves is
[09:39] leaves is the
[09:42] 39,243.7.
[09:47] Lastly, the tree score for the subtree
[09:50] Lastly, the tree score for the subtree with only one leaf is
[09:56] 38,897.2.
[10:01] Note, because alpha equals 10,000 the
[10:04] Note, because alpha equals 10,000 the tree complexity penalty for the tree
[10:06] tree complexity penalty for the tree with one leaf was 10,000.
[10:09] with one leaf was 10,000. And the tree complexity penalty for the
[10:12] And the tree complexity penalty for the tree with two leaves was 20,000.
[10:15] tree with two leaves was 20,000. And the tree complexity penalty for the
[10:17] And the tree complexity penalty for the tree with three leaves was 30,000.
[10:21] tree with three leaves was 30,000. And the tree complexity penalty for the
[10:23] And the tree complexity penalty for the original full-size tree with four leaves
[10:26] original full-size tree with four leaves was 40,000.
[10:29] was 40,000. Thus, the more leaves, the larger the
[10:31] Thus, the more leaves, the larger the penalty.
[10:34] penalty. Now that we have calculated tree scores
[10:36] Now that we have calculated tree scores for all of the trees
[10:39] for all of the trees we pick this subtree because it has the
[10:42] we pick this subtree because it has the lowest tree score.
[10:45] lowest tree score. Double bam.
[10:48] Double bam. Note, if we set alpha equals 22,000
[10:52] Note, if we set alpha equals 22,000 and calculate the tree scores
[10:56] and calculate the tree scores then we would use the subtree with only
[10:59] then we would use the subtree with only one leaf because it has the lowest tree
[11:01] one leaf because it has the lowest tree score.
[11:03] score. Thus, the value for alpha makes a
[11:06] Thus, the value for alpha makes a difference in our choice of subtree.
[11:10] difference in our choice of subtree. So, let's talk about how to build a
[11:11] So, let's talk about how to build a pruned regression tree
[11:14] pruned regression tree and how to find the best value for
[11:16] and how to find the best value for alpha.
[11:18] alpha. First, using all of the data
[11:21] First, using all of the data build a full-sized regression tree.
[11:25] build a full-sized regression tree. Note, this full-size tree is different
[11:28] Note, this full-size tree is different than before because it was fit to all of
[11:30] than before because it was fit to all of the data, not just the training data.
[11:34] the data, not just the training data. Also, note this full-size tree has the
[11:37] Also, note this full-size tree has the lowest tree score when alpha equals
[11:40] lowest tree score when alpha equals zero.
[11:41] zero. This is because when alpha equals zero,
[11:44] This is because when alpha equals zero, the tree complexity penalty becomes
[11:47] the tree complexity penalty becomes zero.
[11:48] zero. And the tree score is just the sum of
[11:51] And the tree score is just the sum of the squared residuals.
[11:53] the squared residuals. And as we saw earlier, all of the
[11:56] And as we saw earlier, all of the subtrees will have larger sum of squared
[11:58] subtrees will have larger sum of squared residuals.
[12:01] residuals. So, let's put alpha equals zero here to
[12:04] So, let's put alpha equals zero here to remind us that this tree has the lowest
[12:06] remind us that this tree has the lowest tree score when alpha equals zero.
[12:10] tree score when alpha equals zero. Now, we will increase alpha until
[12:13] Now, we will increase alpha until pruning leaves will give us a lower tree
[12:15] pruning leaves will give us a lower tree score.
[12:17] score. In this case, when alpha equals 10,000,
[12:20] In this case, when alpha equals 10,000, we'll get a lower tree score if we
[12:23] we'll get a lower tree score if we remove these leaves
[12:25] remove these leaves and use this subtree.
[12:28] and use this subtree. Now, we increase alpha again until
[12:30] Now, we increase alpha again until pruning leaves will give us a lower tree
[12:32] pruning leaves will give us a lower tree score.
[12:34] score. In this case, when alpha equals 15,000,
[12:38] In this case, when alpha equals 15,000, we will get a lower tree score if we
[12:40] we will get a lower tree score if we remove these leaves
[12:43] remove these leaves and use this subtree instead.
[12:46] and use this subtree instead. And when alpha equals 22,000, we will
[12:49] And when alpha equals 22,000, we will get a lower tree score if we remove
[12:51] get a lower tree score if we remove these leaves
[12:53] these leaves and use this subtree instead.
[12:57] and use this subtree instead. In the end, different values for alpha
[13:00] In the end, different values for alpha give us a sequence of trees from
[13:02] give us a sequence of trees from full-sized to just a leaf.
[13:06] full-sized to just a leaf. Now, go back to the full data set
[13:09] Now, go back to the full data set and divide it into training
[13:11] and divide it into training and testing data sets.
[13:14] and testing data sets. And just using the training data,
[13:17] And just using the training data, use the alpha values we found before to
[13:20] use the alpha values we found before to build a full tree and a sequence of
[13:22] build a full tree and a sequence of subtrees that minimize the tree score.
[13:26] subtrees that minimize the tree score. In other words, when alpha equals zero,
[13:29] In other words, when alpha equals zero, we build a full-size tree since it will
[13:32] we build a full-size tree since it will have the lowest tree score.
[13:34] have the lowest tree score. However, when alpha equals 10,000, we
[13:38] However, when alpha equals 10,000, we will get a lower tree score if we prune
[13:40] will get a lower tree score if we prune these leaves
[13:42] these leaves and use this tree instead.
[13:45] and use this tree instead. And when alpha equals 15,000,
[13:48] And when alpha equals 15,000, we will get a lower tree score if we
[13:50] we will get a lower tree score if we prune these leaves
[13:52] prune these leaves and use this tree instead.
[13:55] and use this tree instead. Lastly, when alpha equals 22,000, we
[13:59] Lastly, when alpha equals 22,000, we will get a lower tree score if we prune
[14:01] will get a lower tree score if we prune these two leaves
[14:03] these two leaves and use this tree instead.
[14:07] and use this tree instead. Now calculate the sum of squared
[14:09] Now calculate the sum of squared residuals for each new tree using only
[14:12] residuals for each new tree using only the testing data.
[14:15] the testing data. In this case, the tree with alpha equals
[14:17] In this case, the tree with alpha equals 10,000 had the smallest sum of squared
[14:20] 10,000 had the smallest sum of squared residuals for the testing data.
[14:24] residuals for the testing data. Now we go back and create new training
[14:26] Now we go back and create new training data
[14:27] data and new testing data.
[14:30] and new testing data. And just using the new training data,
[14:34] And just using the new training data, build a new sequence of trees from
[14:36] build a new sequence of trees from full-sized to a leaf using the alpha
[14:39] full-sized to a leaf using the alpha values we found before.
[14:42] values we found before. Then we calculate the sum of squared
[14:44] Then we calculate the sum of squared residuals using the new testing data.
[14:49] residuals using the new testing data. This time, the tree with alpha equals
[14:51] This time, the tree with alpha equals zero had the lowest sum of squared
[14:53] zero had the lowest sum of squared residuals.
[14:55] residuals. Now we just keep repeating until we have
[14:58] Now we just keep repeating until we have done 10-fold cross-validation.
[15:02] done 10-fold cross-validation. And the value for alpha that, on
[15:04] And the value for alpha that, on average, gave us the lowest sum of
[15:06] average, gave us the lowest sum of squared residuals with the testing data
[15:09] squared residuals with the testing data is the final value for alpha.
[15:12] is the final value for alpha. In this case, the optimal trees built
[15:15] In this case, the optimal trees built with alpha equals 10,000 had, on
[15:18] with alpha equals 10,000 had, on average, the lowest sum of squared
[15:20] average, the lowest sum of squared residuals.
[15:22] residuals. So, alpha equals 10,000 is our final
[15:25] So, alpha equals 10,000 is our final value.
[15:27] value. Lastly, we go back to the original trees
[15:30] Lastly, we go back to the original trees and subtrees made from the full data
[15:34] and subtrees made from the full data and pick the tree that corresponds to
[15:36] and pick the tree that corresponds to the value for alpha that we selected.
[15:40] the value for alpha that we selected. This subtree will be the final pruned
[15:43] This subtree will be the final pruned tree.
[15:44] tree. Triple bam!
[15:48] Triple bam! Hooray! We've made it to the end of
[15:50] Hooray! We've made it to the end of another exciting StatQuest.
[15:53] another exciting StatQuest. If you like this StatQuest and want to
[15:55] If you like this StatQuest and want to see more, please subscribe. And if you
[15:57] see more, please subscribe. And if you want to support StatQuest, consider
[15:59] want to support StatQuest, consider contributing to my Patreon campaign,
[16:02] contributing to my Patreon campaign, becoming a channel member, buying one or
[16:04] becoming a channel member, buying one or two of my original songs, or a t-shirt,
[16:06] two of my original songs, or a t-shirt, or a hoodie, or just donate. The links
[16:09] or a hoodie, or just donate. The links are in the description below. All right,
[16:12] are in the description below. All right, until next time, quest on.

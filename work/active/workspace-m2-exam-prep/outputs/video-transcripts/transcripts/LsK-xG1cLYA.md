---
video_id: LsK-xG1cLYA
url: https://www.youtube.com/watch?v=LsK-xG1cLYA
title: AdaBoost, Clearly Explained
channel: StatQuest with Josh Starmer
duration: 20:54
language: en
unit: L12
status: OK
---

[00:00] Machine learning sounds so complicated,
[00:06] learning sounds so complicated, but it's not so complicated.
[00:09] but it's not so complicated. StatQuest.
[00:11] StatQuest. Hello, I'm Josh Starmer, and welcome to
[00:14] Hello, I'm Josh Starmer, and welcome to StatQuest. Today, we're going to cover
[00:16] StatQuest. Today, we're going to cover AdaBoost, and it's going to be clearly
[00:18] AdaBoost, and it's going to be clearly explained.
[00:20] explained. Note, this StatQuest shows how to
[00:22] Note, this StatQuest shows how to combine AdaBoost with decision trees,
[00:25] combine AdaBoost with decision trees, because that is the most common way to
[00:27] because that is the most common way to use AdaBoost. So, if you're not familiar
[00:30] use AdaBoost. So, if you're not familiar with decision trees, check out the
[00:32] with decision trees, check out the quest.
[00:33] quest. We will also mention random forests, so
[00:36] We will also mention random forests, so if you don't know about them, check out
[00:38] if you don't know about them, check out the quest.
[00:39] the quest. We'll start by using decision trees and
[00:42] We'll start by using decision trees and random forests to explain the three
[00:44] random forests to explain the three concepts behind AdaBoost.
[00:47] concepts behind AdaBoost. Then, we'll get into the nitty-gritty
[00:48] Then, we'll get into the nitty-gritty details of how AdaBoost creates a forest
[00:51] details of how AdaBoost creates a forest of trees from scratch, and how it's used
[00:53] of trees from scratch, and how it's used to make classifications.
[00:56] to make classifications. So, let's start by using decision trees
[00:58] So, let's start by using decision trees and random forests to explain the three
[01:01] and random forests to explain the three main concepts behind AdaBoost.
[01:04] main concepts behind AdaBoost. In a random forest, each time you make a
[01:07] In a random forest, each time you make a tree, you make a full-sized tree.
[01:11] tree, you make a full-sized tree. Some trees might be bigger than others,
[01:14] Some trees might be bigger than others, but there's no predetermined maximum
[01:16] but there's no predetermined maximum depth.
[01:17] depth. In contrast, in a forest of trees made
[01:20] In contrast, in a forest of trees made with AdaBoost, the trees are usually
[01:22] with AdaBoost, the trees are usually just a node and two leaves.
[01:26] just a node and two leaves. Oh, no, it's the dreaded terminology
[01:29] Oh, no, it's the dreaded terminology alert.
[01:31] alert. A tree with just one node and two leaves
[01:33] A tree with just one node and two leaves is called a stump.
[01:36] is called a stump. So, this is really a forest of stumps
[01:38] So, this is really a forest of stumps rather than trees.
[01:40] rather than trees. Stumps are not great at making accurate
[01:43] Stumps are not great at making accurate classifications.
[01:45] classifications. For example, if we were using this data
[01:48] For example, if we were using this data to determine if someone had heart
[01:50] to determine if someone had heart disease or not,
[01:52] disease or not, then a full-sized decision tree would
[01:54] then a full-sized decision tree would take advantage of all four variables
[01:56] take advantage of all four variables that we measured, chest pain, blood
[01:58] that we measured, chest pain, blood circulation, blocked arteries, and
[02:00] circulation, blocked arteries, and weight, to make a decision.
[02:03] weight, to make a decision. But, a stump can only use one variable
[02:05] But, a stump can only use one variable to make a decision.
[02:07] to make a decision. Thus, stumps are technically weak
[02:10] Thus, stumps are technically weak learners.
[02:12] learners. However, that's the way AdaBoost likes
[02:14] However, that's the way AdaBoost likes it, and it's one of the reasons why they
[02:16] it, and it's one of the reasons why they are so commonly combined.
[02:19] are so commonly combined. Now, back to the random forest.
[02:22] Now, back to the random forest. In a random forest, each tree has an
[02:25] In a random forest, each tree has an equal vote on the final classification.
[02:29] equal vote on the final classification. This tree's vote is worth just as much
[02:31] This tree's vote is worth just as much as this tree's vote, or this tree's
[02:34] as this tree's vote, or this tree's vote.
[02:35] vote. In contrast, in a forest of stumps made
[02:38] In contrast, in a forest of stumps made with AdaBoost, some stumps get more say
[02:41] with AdaBoost, some stumps get more say in the final classification than others.
[02:44] in the final classification than others. In this illustration, the larger stumps
[02:47] In this illustration, the larger stumps get more say in the final classification
[02:50] get more say in the final classification than the smaller stumps.
[02:53] than the smaller stumps. Lastly, in a random forest, each
[02:56] Lastly, in a random forest, each decision tree is made independently of
[02:58] decision tree is made independently of the others.
[03:00] the others. In other words, it doesn't matter if
[03:02] In other words, it doesn't matter if this tree was made first, or this one.
[03:06] this tree was made first, or this one. In contrast, in a forest of stumps made
[03:09] In contrast, in a forest of stumps made with AdaBoost, order is important.
[03:13] with AdaBoost, order is important. The errors that the first stump makes
[03:16] The errors that the first stump makes influence how the second stump is made.
[03:19] influence how the second stump is made. And the errors that the second stump
[03:21] And the errors that the second stump makes
[03:22] makes influence how the third stump is made.
[03:26] influence how the third stump is made. Etcetera, etcetera, etcetera.
[03:30] Etcetera, etcetera, etcetera. To review, the three ideas behind
[03:33] To review, the three ideas behind AdaBoost are:
[03:35] AdaBoost are: One, AdaBoost combines a lot of weak
[03:37] One, AdaBoost combines a lot of weak learners to make classifications.
[03:40] learners to make classifications. The weak learners are almost always
[03:42] The weak learners are almost always stumps.
[03:44] stumps. Two, some stumps get more say in the
[03:46] Two, some stumps get more say in the classification than others.
[03:49] classification than others. Three, each stump is made by taking the
[03:52] Three, each stump is made by taking the previous stumps mistakes into account.
[03:56] previous stumps mistakes into account. Bam!
[03:59] Bam! Now, let's dive into the nitty-gritty
[04:01] Now, let's dive into the nitty-gritty detail of how to create a forest of
[04:03] detail of how to create a forest of stumps using AdaBoost.
[04:06] stumps using AdaBoost. First, we'll start with some data.
[04:09] First, we'll start with some data. We create a forest of stumps with
[04:11] We create a forest of stumps with AdaBoost to predict if a patient has
[04:13] AdaBoost to predict if a patient has heart disease.
[04:15] heart disease. We will make these predictions based on
[04:17] We will make these predictions based on a patient's chest pain and blocked
[04:19] a patient's chest pain and blocked artery status and their weight.
[04:22] artery status and their weight. The first thing we do is give each
[04:24] The first thing we do is give each sample a weight that indicates how
[04:26] sample a weight that indicates how important it is to be correctly
[04:28] important it is to be correctly classified.
[04:30] classified. Note, the sample weight is different
[04:32] Note, the sample weight is different from the patient weight, and I'll do the
[04:34] from the patient weight, and I'll do the best I can to be clear about which of
[04:36] best I can to be clear about which of the two I'm talking about.
[04:39] the two I'm talking about. At the start, all samples get the same
[04:42] At the start, all samples get the same weight.
[04:43] weight. One divided by the total number of
[04:46] One divided by the total number of samples.
[04:47] samples. In this case, that's one divided by
[04:50] In this case, that's one divided by eight.
[04:51] eight. And that makes the samples all equally
[04:53] And that makes the samples all equally important.
[04:56] important. However, after we make the first stump,
[04:58] However, after we make the first stump, these weights will change in order to
[05:00] these weights will change in order to guide how the next stump is created.
[05:03] guide how the next stump is created. In other words, we'll talk more about
[05:05] In other words, we'll talk more about the sample weights later.
[05:08] the sample weights later. Now, we need to make the first stump in
[05:10] Now, we need to make the first stump in the forest.
[05:12] the forest. This is done by finding the variable
[05:15] This is done by finding the variable chest pain, blocked arteries, or patient
[05:17] chest pain, blocked arteries, or patient weight that does the best job
[05:19] weight that does the best job classifying the samples.
[05:22] classifying the samples. Note, because all of the weights are the
[05:24] Note, because all of the weights are the same, we can ignore them right now.
[05:28] same, we can ignore them right now. We start by seeing how well chest pain
[05:31] We start by seeing how well chest pain classifies the samples.
[05:34] classifies the samples. Of the five samples with chest pain,
[05:36] Of the five samples with chest pain, three were correctly classified as
[05:38] three were correctly classified as having heart disease.
[05:40] having heart disease. And two were incorrectly classified.
[05:44] And two were incorrectly classified. Of the three samples without chest pain,
[05:47] Of the three samples without chest pain, two were correctly classified as not
[05:49] two were correctly classified as not having heart disease.
[05:52] having heart disease. And one was incorrectly classified.
[05:56] And one was incorrectly classified. Now we do the same thing for blocked
[05:58] Now we do the same thing for blocked arteries.
[06:00] arteries. And for patient weight.
[06:03] And for patient weight. Note, we used the techniques described
[06:05] Note, we used the techniques described in the decision tree StatQuest to
[06:07] in the decision tree StatQuest to determine that 176 was the best weight
[06:11] determine that 176 was the best weight to separate the patients.
[06:14] to separate the patients. Now we calculate the Gini index for the
[06:16] Now we calculate the Gini index for the three stumps.
[06:19] three stumps. The Gini index for patient weight is the
[06:22] The Gini index for patient weight is the lowest.
[06:23] lowest. So this will be the first stump in the
[06:25] So this will be the first stump in the forest.
[06:27] forest. Now we need to determine how much say
[06:30] Now we need to determine how much say this stump will have in the final
[06:31] this stump will have in the final classification.
[06:33] classification. Remember, some stumps get more say in
[06:36] Remember, some stumps get more say in the final classification than others.
[06:40] the final classification than others. We determine how much say a stump has in
[06:42] We determine how much say a stump has in the final classification based on how
[06:45] the final classification based on how well it classified the samples.
[06:48] well it classified the samples. This stump made one error.
[06:52] This stump made one error. This patient, who weighs less than 176,
[06:55] This patient, who weighs less than 176, has heart disease, but the stump says
[06:58] has heart disease, but the stump says they do not.
[07:01] they do not. The total error for a stump is the sum
[07:03] The total error for a stump is the sum of the weights associated with the
[07:05] of the weights associated with the incorrectly classified samples.
[07:09] incorrectly classified samples. Thus, in this case, the total error is
[07:12] Thus, in this case, the total error is 1/8.
[07:14] 1/8. Note, because all of the sample weights
[07:17] Note, because all of the sample weights add up to one, total error will always
[07:20] add up to one, total error will always be between zero for a perfect stump and
[07:23] be between zero for a perfect stump and one for a horrible stump.
[07:27] one for a horrible stump. We use the total error to determine the
[07:29] We use the total error to determine the amount of say this stump has in the
[07:31] amount of say this stump has in the final classification with the following
[07:33] final classification with the following formula.
[07:35] formula. Amount of say equals 1/2 times the log
[07:39] Amount of say equals 1/2 times the log of 1 minus the total error divided by
[07:42] of 1 minus the total error divided by the total error.
[07:44] the total error. We can draw a graph of the amount of say
[07:47] We can draw a graph of the amount of say by plugging in a bunch of numbers
[07:48] by plugging in a bunch of numbers between zero and one for total error.
[07:52] between zero and one for total error. The blue line tells us the amount of say
[07:55] The blue line tells us the amount of say for total error values between zero and
[07:57] for total error values between zero and one.
[07:59] one. When a stump does a good job and the
[08:01] When a stump does a good job and the total error is small,
[08:04] total error is small, then the amount of say is a relatively
[08:06] then the amount of say is a relatively large positive value.
[08:10] large positive value. When a stump is no better at
[08:11] When a stump is no better at classification than flipping a coin,
[08:13] classification than flipping a coin, i.e. half the stumps are correctly
[08:16] i.e. half the stumps are correctly classified and half are incorrectly
[08:18] classified and half are incorrectly classified, and the total error equals
[08:20] classified, and the total error equals 0.5,
[08:22] 0.5, then the amount of say will be zero.
[08:26] then the amount of say will be zero. And when a stump does a terrible job and
[08:29] And when a stump does a terrible job and the total error is close to one,
[08:31] the total error is close to one, in other words, if the stump
[08:33] in other words, if the stump consistently gives you the opposite
[08:35] consistently gives you the opposite classification,
[08:37] classification, then the amount of say will be a large
[08:40] then the amount of say will be a large negative value.
[08:42] negative value. So if a stump votes for heart disease,
[08:44] So if a stump votes for heart disease, the negative amount of say will turn
[08:47] the negative amount of say will turn that vote into not heart disease.
[08:51] that vote into not heart disease. Note, if total error is one or zero,
[08:54] Note, if total error is one or zero, then this equation will freak out.
[08:57] then this equation will freak out. In practice, a small error term is added
[09:00] In practice, a small error term is added to prevent this from happening.
[09:03] to prevent this from happening. With patient weight greater than 176,
[09:07] With patient weight greater than 176, the total error is 1/8, so we just plug
[09:10] the total error is 1/8, so we just plug and chug.
[09:14] And the amount of say that this stump has on the final classification is 0.97.
[09:21] has on the final classification is 0.97. Bam!
[09:23] Bam! Now that we've worked out how much say
[09:25] Now that we've worked out how much say this stump gets when classifying a
[09:27] this stump gets when classifying a sample,
[09:28] sample, let's work out how much say the chest
[09:30] let's work out how much say the chest pain stump would have if it had been the
[09:33] pain stump would have if it had been the best stump.
[09:34] best stump. Note, we don't need to do this, but I
[09:37] Note, we don't need to do this, but I think it helps illustrate the concepts
[09:39] think it helps illustrate the concepts we've covered so far.
[09:41] we've covered so far. Chest pain made three errors.
[09:45] Chest pain made three errors. And the total error equals the sum of
[09:47] And the total error equals the sum of the weights for the incorrectly
[09:49] the weights for the incorrectly classified samples.
[09:54] So, the total error for chest pain is 3/8.
[09:58] 3/8. We can get a sense of what the amount of
[10:00] We can get a sense of what the amount of say will be by looking at the graph when
[10:03] say will be by looking at the graph when total error equals 3/8.
[10:06] total error equals 3/8. So, we are expecting the amount of say
[10:08] So, we are expecting the amount of say to be between 0 and 0.5.
[10:12] to be between 0 and 0.5. Now, we plug 3/8 into the formula for
[10:15] Now, we plug 3/8 into the formula for the amount of say and do the math.
[10:21] And the amount of say that the chest pain stump would have had on the final
[10:25] pain stump would have had on the final classification is 0.42.
[10:29] classification is 0.42. I'll leave the blocked artery stump as
[10:32] I'll leave the blocked artery stump as an exercise for the viewer.
[10:34] an exercise for the viewer. Now, we know how the sample weights for
[10:36] Now, we know how the sample weights for the incorrectly classified samples are
[10:39] the incorrectly classified samples are used to determine the amount of say each
[10:42] used to determine the amount of say each stump gets.
[10:43] stump gets. Bam!
[10:46] Bam! Now, we need to learn how to modify the
[10:48] Now, we need to learn how to modify the weights so that the next stump will take
[10:50] weights so that the next stump will take the errors that the current stump made
[10:52] the errors that the current stump made into account.
[10:55] into account. Let's go back to the first stump that we
[10:57] Let's go back to the first stump that we made.
[10:59] made. When we created this stump, all of the
[11:01] When we created this stump, all of the sample weights were the same.
[11:04] sample weights were the same. And that meant we did not emphasize the
[11:06] And that meant we did not emphasize the importance of correctly classifying any
[11:09] importance of correctly classifying any particular sample.
[11:11] particular sample. But, since this stump incorrectly
[11:13] But, since this stump incorrectly classified this sample,
[11:16] classified this sample, we will emphasize the need for the next
[11:18] we will emphasize the need for the next stump to correctly classify it by
[11:20] stump to correctly classify it by increasing its sample weight
[11:23] increasing its sample weight and decreasing all of the other sample
[11:26] and decreasing all of the other sample weights.
[11:28] weights. Let's start by increasing the sample
[11:31] Let's start by increasing the sample weight for the incorrectly classified
[11:33] weight for the incorrectly classified sample.
[11:35] sample. This is the formula we will use to
[11:37] This is the formula we will use to increase the sample weight for the
[11:39] increase the sample weight for the sample that was incorrectly classified.
[11:43] sample that was incorrectly classified. We plug in the sample weight from the
[11:45] We plug in the sample weight from the last stump
[11:47] last stump and we scale 1/8 with this term.
[11:51] and we scale 1/8 with this term. To get a better understanding of how
[11:53] To get a better understanding of how this part will scale the previous sample
[11:55] this part will scale the previous sample weight, let's draw a graph.
[11:58] weight, let's draw a graph. The blue line is equal to e raised to
[12:01] The blue line is equal to e raised to the amount of say.
[12:04] the amount of say. When the amount of say is relatively
[12:06] When the amount of say is relatively large, i.e. the last stump did a good
[12:09] large, i.e. the last stump did a good job classifying samples,
[12:11] job classifying samples, then we will scale the previous sample
[12:13] then we will scale the previous sample weight with a large number.
[12:16] weight with a large number. This means that the new sample weight
[12:19] This means that the new sample weight will be much larger than the old one.
[12:22] will be much larger than the old one. And when the amount of say is relatively
[12:25] And when the amount of say is relatively low, i.e. the last stump did not do a
[12:28] low, i.e. the last stump did not do a very good job classifying samples,
[12:31] very good job classifying samples, then the previous sample weight is
[12:33] then the previous sample weight is scaled by a relatively small number.
[12:36] scaled by a relatively small number. This means that the new sample weight
[12:39] This means that the new sample weight will only be a little larger than the
[12:41] will only be a little larger than the old one.
[12:43] old one. In this example, the amount of say was
[12:46] In this example, the amount of say was 0.97.
[12:48] 0.97. And e raised to the 0.97
[12:52] And e raised to the 0.97 equals 2.64.
[12:55] equals 2.64. That means the new sample weight is
[12:58] That means the new sample weight is 0.33,
[12:59] 0.33, which is more than the old one.
[13:02] which is more than the old one. Bam.
[13:04] Bam. Now we need to decrease the sample
[13:06] Now we need to decrease the sample weights for all of the correctly
[13:08] weights for all of the correctly classified samples.
[13:11] classified samples. This is the formula we will use to
[13:12] This is the formula we will use to decrease the sample weights.
[13:16] decrease the sample weights. The big difference is the negative sign
[13:18] The big difference is the negative sign in front of amount of say.
[13:22] in front of amount of say. Just like before, we plug in the sample
[13:24] Just like before, we plug in the sample weight.
[13:26] weight. And just like before, we can get a
[13:28] And just like before, we can get a better understanding of how this will
[13:30] better understanding of how this will scale the sample weight by plotting a
[13:32] scale the sample weight by plotting a graph using different values for amount
[13:34] graph using different values for amount of say.
[13:36] of say. The blue line represents e raised to the
[13:39] The blue line represents e raised to the negative amount of say.
[13:42] negative amount of say. When the amount of say is relatively
[13:44] When the amount of say is relatively large,
[13:46] large, then we scale the sample weight by a
[13:48] then we scale the sample weight by a value close to zero.
[13:51] value close to zero. This will make the new sample weight
[13:53] This will make the new sample weight very small.
[13:55] very small. If the amount of say for the last stump
[13:57] If the amount of say for the last stump is relatively small,
[14:00] is relatively small, then we will scale the sample weight by
[14:02] then we will scale the sample weight by a value close to one.
[14:05] a value close to one. This means that the new sample weight
[14:07] This means that the new sample weight will be just a little smaller than the
[14:09] will be just a little smaller than the old one.
[14:11] old one. In this example, the amount of say was
[14:13] In this example, the amount of say was 0.97.
[14:16] 0.97. And e raised to the negative 0.97
[14:19] And e raised to the negative 0.97 equals 0.38.
[14:23] equals 0.38. The new sample weight is 0.05,
[14:26] The new sample weight is 0.05, which is less than the old one.
[14:29] which is less than the old one. Bam.
[14:31] Bam. We will keep track of the new sample
[14:33] We will keep track of the new sample weights in this column.
[14:36] weights in this column. We plug in 0.33
[14:39] We plug in 0.33 for the sample that was incorrectly
[14:40] for the sample that was incorrectly classified.
[14:42] classified. All of the other samples get 0.05.
[14:47] Now we need to normalize the new sample weights so that they will add up to one.
[14:53] weights so that they will add up to one. Right now, if you add up the new sample
[14:55] Right now, if you add up the new sample weights, you get 0.68.
[14:59] So we divide each new sample weight by
[15:02] So we divide each new sample weight by 0.68
[15:03] 0.68 to get the normalized values.
[15:07] to get the normalized values. Now, when we add up the new sample
[15:09] Now, when we add up the new sample weights, we get one, plus or minus a
[15:11] weights, we get one, plus or minus a little rounding error.
[15:14] little rounding error. Now we just transfer the normalized
[15:16] Now we just transfer the normalized sample weights to the sample weights
[15:18] sample weights to the sample weights column, since those are what we will use
[15:20] column, since those are what we will use for the next stump.
[15:23] for the next stump. Now we can use the modified sample
[15:25] Now we can use the modified sample weights to make the second stump in the
[15:27] weights to make the second stump in the forest.
[15:29] forest. Bam!
[15:32] In theory, we could use the sample weights to calculate weighted Gini
[15:36] weights to calculate weighted Gini indexes to determine which variable
[15:39] indexes to determine which variable should split the next stump.
[15:41] should split the next stump. The weighted Gini index would put more
[15:43] The weighted Gini index would put more emphasis on correctly classifying this
[15:46] emphasis on correctly classifying this sample,
[15:47] sample, the one that was misclassified by the
[15:49] the one that was misclassified by the last stump, since this sample has the
[15:51] last stump, since this sample has the largest sample weight.
[15:54] largest sample weight. Alternatively, instead of using a
[15:57] Alternatively, instead of using a weighted Gini index, we can make a new
[15:59] weighted Gini index, we can make a new collection of samples that contains
[16:01] collection of samples that contains duplicate copies of the samples with the
[16:04] duplicate copies of the samples with the largest sample weights.
[16:07] largest sample weights. So we start by making a new, but empty,
[16:09] So we start by making a new, but empty, data set that is the same size as the
[16:12] data set that is the same size as the original.
[16:14] original. Then we pick a random number between 0
[16:16] Then we pick a random number between 0 and 1.
[16:18] and 1. And we see where that number falls when
[16:21] And we see where that number falls when we use the sample weights like a
[16:22] we use the sample weights like a distribution.
[16:25] distribution. If the number is between 0 and 0.7,
[16:28] If the number is between 0 and 0.7, then we would put this sample into the
[16:30] then we would put this sample into the new collection of samples.
[16:33] new collection of samples. And if the number is between 0.7 and
[16:36] And if the number is between 0.7 and 0.14,
[16:38] 0.14, then we would put this sample into the
[16:40] then we would put this sample into the new collection of samples.
[16:42] new collection of samples. And if the number is between 0.14
[16:45] And if the number is between 0.14 and 0.21,
[16:47] and 0.21, then we would put this sample into the
[16:49] then we would put this sample into the new collection of samples.
[16:52] new collection of samples. And if the number is between 0.21
[16:55] And if the number is between 0.21 and 0.70,
[16:57] and 0.70, then we would put this sample into the
[16:59] then we would put this sample into the new collection of samples.
[17:01] new collection of samples. Et cetera, et cetera.
[17:04] Et cetera, et cetera. For example, imagine the first number I
[17:07] For example, imagine the first number I picked was 0.72.
[17:10] picked was 0.72. Then I would put this sample into my new
[17:12] Then I would put this sample into my new collection of samples.
[17:15] collection of samples. Then I pick another random number and
[17:17] Then I pick another random number and get 0.42.
[17:20] get 0.42. And I would put this sample into my new
[17:23] And I would put this sample into my new collection of samples.
[17:25] collection of samples. Then I pick 0.83.
[17:28] Then I pick 0.83. And I would put this sample into my new
[17:30] And I would put this sample into my new collection of samples.
[17:33] collection of samples. Then I pick 0.51.
[17:36] Then I pick 0.51. And I would put this sample into my new
[17:38] And I would put this sample into my new collection of samples.
[17:41] collection of samples. Note, this is the second time we have
[17:44] Note, this is the second time we have added this particular sample to the new
[17:46] added this particular sample to the new collection of samples.
[17:49] collection of samples. We then continue to pick random numbers
[17:51] We then continue to pick random numbers and add samples to the new collection
[17:53] and add samples to the new collection until the new collection is the same
[17:55] until the new collection is the same size as the original.
[17:58] size as the original. Ultimately, this sample was added to the
[18:01] Ultimately, this sample was added to the new collection of samples four times,
[18:03] new collection of samples four times, reflecting its larger sample weight.
[18:07] reflecting its larger sample weight. Now we get rid of the original samples
[18:11] Now we get rid of the original samples and use the new collection of samples.
[18:15] and use the new collection of samples. Lastly, we give all of the samples equal
[18:17] Lastly, we give all of the samples equal sample weights, just like before.
[18:21] sample weights, just like before. However, that doesn't mean the next
[18:23] However, that doesn't mean the next stump will not emphasize the need to
[18:25] stump will not emphasize the need to correctly classify these samples.
[18:29] correctly classify these samples. Because these samples are all the same,
[18:31] Because these samples are all the same, they will be treated as a block,
[18:33] they will be treated as a block, creating a large penalty for being
[18:35] creating a large penalty for being misclassified.
[18:38] Now we go back to the beginning and try to find the stump that does the best job
[18:42] to find the stump that does the best job classifying the new collection of
[18:44] classifying the new collection of samples.
[18:46] samples. So that is how the errors that the first
[18:48] So that is how the errors that the first tree makes
[18:50] tree makes influence how the second tree is made.
[18:53] influence how the second tree is made. And how the errors that the second tree
[18:55] And how the errors that the second tree makes
[18:56] makes influence how the third tree is made.
[19:00] influence how the third tree is made. Etcetera, etcetera, etcetera.
[19:03] Etcetera, etcetera, etcetera. Double bam!
[19:06] Double bam! Now we need to talk about how a forest
[19:08] Now we need to talk about how a forest of stumps created by AdaBoost makes
[19:11] of stumps created by AdaBoost makes classifications.
[19:13] classifications. Imagine that these stumps classified a
[19:15] Imagine that these stumps classified a patient as has heart disease.
[19:19] patient as has heart disease. And these stumps classified the patient
[19:21] And these stumps classified the patient as does not have heart disease.
[19:25] as does not have heart disease. These are the amounts of say for these
[19:27] These are the amounts of say for these stumps.
[19:29] stumps. And these are the amounts of say for
[19:31] And these are the amounts of say for these stumps.
[19:33] these stumps. Now we add up the amounts of say for
[19:35] Now we add up the amounts of say for this group of stumps
[19:37] this group of stumps and for this group of stumps.
[19:40] and for this group of stumps. Ultimately, the patient is classified as
[19:43] Ultimately, the patient is classified as has heart disease because this is the
[19:46] has heart disease because this is the larger sum.
[19:48] larger sum. Triple bam!
[19:51] Triple bam! To review, the three ideas behind
[19:54] To review, the three ideas behind AdaBoost are
[19:56] AdaBoost are one, AdaBoost combines a lot of weak
[19:59] one, AdaBoost combines a lot of weak learners to make classifications.
[20:01] learners to make classifications. The weak learners are almost always
[20:04] The weak learners are almost always stumps.
[20:05] stumps. Two, some stumps get more say in the
[20:08] Two, some stumps get more say in the classification than others.
[20:11] classification than others. And three, each stump is made by taking
[20:14] And three, each stump is made by taking the previous stumps mistakes into
[20:16] the previous stumps mistakes into account.
[20:18] account. If we have a weighted gini function,
[20:20] If we have a weighted gini function, then we use it with the sample weights.
[20:22] then we use it with the sample weights. Otherwise, we use the sample weights to
[20:25] Otherwise, we use the sample weights to make a new data set that reflects those
[20:27] make a new data set that reflects those weights.
[20:29] weights. Hooray! We've made it to the end of
[20:31] Hooray! We've made it to the end of another exciting StatQuest. If you like
[20:34] another exciting StatQuest. If you like this StatQuest and want to see more,
[20:36] this StatQuest and want to see more, please subscribe.
[20:37] please subscribe. And if you want to support StatQuest,
[20:39] And if you want to support StatQuest, well, consider buying a t-shirt or a
[20:41] well, consider buying a t-shirt or a hoodie, or buying one or two of my
[20:43] hoodie, or buying one or two of my original songs. The links to do this are
[20:46] original songs. The links to do this are in the description below.
[20:48] in the description below. All right, until next time, quest on.

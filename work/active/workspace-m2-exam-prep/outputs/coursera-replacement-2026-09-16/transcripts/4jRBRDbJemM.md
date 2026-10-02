---
video_id: 4jRBRDbJemM
url: https://www.youtube.com/watch?v=4jRBRDbJemM
title: ROC and AUC, Clearly Explained!
channel: StatQuest with Josh Starmer
duration: 16:17
language: en
unit: L11
status: OK
---

[00:00] Wait till you see
[00:03] Wait till you see the R [music] O
[00:06] the R [music] O and the A.
[00:09] and the A. They're [music] cool. [singing] Yeah.
[00:10] They're [music] cool. [singing] Yeah. Stack Quest.
[00:13] Stack Quest. Hello, I'm Josh Starmer and welcome to
[00:16] Hello, I'm Josh Starmer and welcome to Stack Quest. Today we're going to talk
[00:18] Stack Quest. Today we're going to talk about ROC and AU and they're going to be
[00:21] about ROC and AU and they're going to be clearly explained.
[00:23] clearly explained. Note, this stat quest builds on the
[00:26] Note, this stat quest builds on the confusion matrix and sensitivity and
[00:28] confusion matrix and sensitivity and specificity stat quests. So, if you're
[00:30] specificity stat quests. So, if you're not already down with those, check out
[00:32] not already down with those, check out the quests.
[00:34] the quests. Also, the example I give in this stat
[00:37] Also, the example I give in this stat quest is based on logistic regression.
[00:39] quest is based on logistic regression. So, even though ROC and AU apply to more
[00:43] So, even though ROC and AU apply to more than just logistic regression, make sure
[00:45] than just logistic regression, make sure you understand those basics.
[00:48] you understand those basics. Let's start with some data.
[00:51] Let's start with some data. The yaxis has two categories obese and
[00:55] The yaxis has two categories obese and not obese.
[00:58] not obese. The blue dots represent obese mice and
[01:01] The blue dots represent obese mice and the red dots represent mice that are not
[01:04] the red dots represent mice that are not obese.
[01:06] obese. Along the x-axis we have weight.
[01:09] Along the x-axis we have weight.
[01:10] Along the x-axis we have weight. This mouse is not obese even though it
[01:12] This mouse is not obese even though it weighs a lot. It must be mighty mouse
[01:15] weighs a lot. It must be mighty mouse and just full of muscles.
[01:18] and just full of muscles. This mouse doesn't weigh that much, but
[01:20] This mouse doesn't weigh that much, but it is still considered obese for its
[01:23] it is still considered obese for its size.
[01:24] size. Now, let's fit a logistic regression
[01:26] Now, let's fit a logistic regression curve to the data.
[01:29] curve to the data. When we're doing logistic regression,
[01:31] When we're doing logistic regression, the yaxis is converted to the
[01:33] the yaxis is converted to the probability that a mouse is obese.
[01:37] probability that a mouse is obese. Now, let's just look at the curve.
[01:40] Now, let's just look at the curve. If someone told us that they had a heavy
[01:42] If someone told us that they had a heavy mouse that weighs this much, then the
[01:45] mouse that weighs this much, then the curve would tell us that there is a high
[01:47] curve would tell us that there is a high probability that the mouse is obese.
[01:51] probability that the mouse is obese. If someone told us that they had a light
[01:53] If someone told us that they had a light mouse that weighs this much, then the
[01:56] mouse that weighs this much, then the curve would tell us that there is a low
[01:58] curve would tell us that there is a low probability that the mouse is obese.
[02:01] probability that the mouse is obese. So this logistic regression tells us the
[02:04] So this logistic regression tells us the probability that a mouse is obese based
[02:06] probability that a mouse is obese based on its weight.
[02:08] on its weight. However, if we want to classify the mice
[02:11] However, if we want to classify the mice as obese or not obese, then we need a
[02:14] as obese or not obese, then we need a way to turn probabilities into
[02:16] way to turn probabilities into classifications.
[02:18] classifications. One way to classify mice is to set a
[02:20] One way to classify mice is to set a threshold at 0.5
[02:23] threshold at 0.5
[02:24] threshold at 0.5 and classify all mice with a probability
[02:26] and classify all mice with a probability of being obese greater than 0.5 as
[02:29] of being obese greater than 0.5 as
[02:30] of being obese greater than 0.5 as obese.
[02:31] obese. and classify all mice with a probability
[02:34] and classify all mice with a probability of being obese less than or equal to 0.5
[02:38] of being obese less than or equal to 0.5 as not obese.
[02:40] as not obese. Using 0.5 as the cutoff, we would call
[02:44] Using 0.5 as the cutoff, we would call this mouse obese
[02:46] this mouse obese and this mouse not obese.
[02:50] and this mouse not obese. If another mouse weighed this much, then
[02:53] If another mouse weighed this much, then we would classify it as obese.
[02:55] we would classify it as obese.
[02:56] we would classify it as obese. And if another mouse weighed this much,
[02:58] And if another mouse weighed this much, then we would classify it as not obese.
[03:03] then we would classify it as not obese. To evaluate the effectiveness of this
[03:05] To evaluate the effectiveness of this logistic regression with the
[03:07] logistic regression with the classification threshold set to 0.5, we
[03:10] classification threshold set to 0.5, we can test it with mice that we know are
[03:12] can test it with mice that we know are obese and not obese.
[03:15] obese and not obese. Here are the weights of four new mice
[03:17] Here are the weights of four new mice that we know are not obese.
[03:20] that we know are not obese. And here are the weights of four new
[03:22] And here are the weights of four new mice that we know are obese.
[03:25] mice that we know are obese. We know that this mouse is not obese and
[03:29] We know that this mouse is not obese and the logistic regression with the
[03:31] the logistic regression with the classification threshold set to 0.5
[03:34] classification threshold set to 0.5 correctly classifies it as not obese.
[03:38] correctly classifies it as not obese. This mouse is also correctly classified
[03:42] This mouse is also correctly classified but this mouse is incorrectly
[03:44] but this mouse is incorrectly classified.
[03:46] classified. We know that it is obese but it is
[03:48] We know that it is obese but it is classified as not obese.
[03:52] classified as not obese. The next mouse is correctly classified,
[03:55] The next mouse is correctly classified, but this mouse is incorrectly
[03:57] but this mouse is incorrectly classified.
[03:59] classified. The last three mice are correctly
[04:01] The last three mice are correctly classified.
[04:03] classified. Now we create a confusion matrix to
[04:05] Now we create a confusion matrix to summarize the classifications.
[04:08] summarize the classifications. These three samples were correctly
[04:10] These three samples were correctly classified as obese.
[04:12] classified as obese. And this sample was predicted to be
[04:15] And this sample was predicted to be obese but was not obese.
[04:18] obese but was not obese. These three samples were correctly
[04:20] These three samples were correctly classified as not obese.
[04:24] classified as not obese. And this sample was predicted to be not
[04:26] And this sample was predicted to be not obese even though it was obese.
[04:30] obese even though it was obese. Once the confusion matrix is filled in,
[04:33] Once the confusion matrix is filled in, we can calculate sensitivity and
[04:35] we can calculate sensitivity and specificity to evaluate this logistic
[04:37] specificity to evaluate this logistic regression when 0.5 is the threshold for
[04:41] regression when 0.5 is the threshold for obesity.
[04:43] obesity. Little bam. Because so far this is all
[04:46] Little bam. Because so far this is all review.
[04:48] review. Now let's talk about what happens when
[04:49] Now let's talk about what happens when
[04:50] Now let's talk about what happens when we use a different threshold for
[04:51] we use a different threshold for deciding if a sample is obese or not.
[04:55] deciding if a sample is obese or not. For example, if it was super important
[04:57] For example, if it was super important to correctly classify every obese
[04:59] to correctly classify every obese
[05:00] to correctly classify every obese sample, we could set the threshold to
[05:02] sample, we could set the threshold to 0.1.
[05:04] 0.1. This would result in correct
[05:06] This would result in correct classifications for all four obese mice,
[05:10] classifications for all four obese mice, but it would also increase the number of
[05:12] but it would also increase the number of false positives.
[05:15] false positives. The lower threshold would also reduce
[05:17] The lower threshold would also reduce the number of false negatives because
[05:19] the number of false negatives because all of the obese mice were correctly
[05:21] all of the obese mice were correctly classified.
[05:23] classified. Note, if the idea of using a threshold
[05:26] Note, if the idea of using a threshold other than 0.5 is blowing your mind,
[05:29] other than 0.5 is blowing your mind, imagine that instead of classifying
[05:31] imagine that instead of classifying samples as obese or not obese, we were
[05:34] samples as obese or not obese, we were classifying samples as infected with
[05:37] classifying samples as infected with Ebola and not infected with Ebola.
[05:40] Ebola and not infected with Ebola. In this case, it's absolutely essential
[05:43] In this case, it's absolutely essential to correctly classify every sample
[05:45] to correctly classify every sample infected with Ebola in order to minimize
[05:48] infected with Ebola in order to minimize the risk of an outbreak.
[05:50] the risk of an outbreak. And that means lowering the threshold
[05:53] And that means lowering the threshold even if that results in more false
[05:55] even if that results in more false positives.
[05:57] positives. On the other hand, we could set the
[05:59] On the other hand, we could set the threshold to 0.9.
[06:02] threshold to 0.9. In this case, we would correctly
[06:04] In this case, we would correctly classify the same number of obese
[06:06] classify the same number of obese samples as when the threshold was set to
[06:08] samples as when the threshold was set to 0.5,
[06:11] 0.5, but we wouldn't have any false
[06:13] but we wouldn't have any false positives.
[06:15] positives. And we would correctly classify one more
[06:17] And we would correctly classify one more sample that was not obese
[06:20] sample that was not obese and have the same number of false
[06:22] and have the same number of false negatives as before.
[06:25] negatives as before. With this data, the higher threshold
[06:27] With this data, the higher threshold does a better job classifying samples as
[06:29] does a better job classifying samples as obese or not obese.
[06:32] obese or not obese. But the threshold could be set to
[06:34] But the threshold could be set to anything between zero and one. How do we
[06:38] anything between zero and one. How do we determine which threshold is the best?
[06:42] determine which threshold is the best? For starters, we don't need to test
[06:44] For starters, we don't need to test every single option. For example, these
[06:47] every single option. For example, these thresholds result in the exact same
[06:49] thresholds result in the exact same
[06:50] thresholds result in the exact same confusion matrix.
[06:53] confusion matrix. But even if we made one confusion matrix
[06:55] But even if we made one confusion matrix for each threshold that mattered, it
[06:57] for each threshold that mattered, it would result in a confusingly large
[06:59] would result in a confusingly large number of confusion matrices.
[07:03] number of confusion matrices. So instead of being overwhelmed with
[07:05] So instead of being overwhelmed with confusion matrices, receiver operator
[07:08] confusion matrices, receiver operator characteristic ROC graphs provide a
[07:12] characteristic ROC graphs provide a simple way to summarize all of the
[07:14] simple way to summarize all of the information.
[07:16] information. The yaxis shows the true positive rate,
[07:19] The yaxis shows the true positive rate, which is the same thing as sensitivity.
[07:22] which is the same thing as sensitivity. The true positive rate is the true
[07:25] The true positive rate is the true positives divided by the sum of the true
[07:28] positives divided by the sum of the true positives and the false negatives.
[07:31] positives and the false negatives. In this example, the true positives are
[07:34] In this example, the true positives are the samples that were correctly
[07:35] the samples that were correctly classified as obese.
[07:38] classified as obese. And the false negatives are the obese
[07:40] And the false negatives are the obese samples that were incorrectly classified
[07:43] samples that were incorrectly classified as not obese.
[07:45] as not obese. The true positive rate tells you what
[07:47] The true positive rate tells you what proportion of obese samples were
[07:49] proportion of obese samples were correctly classified.
[07:52] correctly classified. The xaxis shows the false positive rate
[07:56] The xaxis shows the false positive rate which is the same thing as 1 minus
[07:58] which is the same thing as 1 minus specificity.
[08:00] specificity. The false positive rate is the false
[08:02] The false positive rate is the false positives divided by the sum of the
[08:05] positives divided by the sum of the false positives and true negatives.
[08:09] false positives and true negatives. The false positives are the non-obese
[08:11] The false positives are the non-obese samples that were incorrectly classified
[08:13] samples that were incorrectly classified
[08:14] samples that were incorrectly classified as obese.
[08:16] as obese. and the true negatives are the samples
[08:18] and the true negatives are the samples correctly classified as not obese.
[08:22] correctly classified as not obese. The false positive rate tells you the
[08:25] The false positive rate tells you the proportion of not obese samples that
[08:27] proportion of not obese samples that were incorrectly classified and are
[08:29] were incorrectly classified and are false positives.
[08:32] false positives. To get a better sense of how the ROC
[08:34] To get a better sense of how the ROC works, let's draw one from start to
[08:36] works, let's draw one from start to finish using our example data.
[08:39] finish using our example data. We'll start by using a threshold that
[08:42] We'll start by using a threshold that classifies all of the samples as obese.
[08:45] classifies all of the samples as obese. And that gives us this confusion matrix.
[08:50] And that gives us this confusion matrix. First, let's calculate the true positive
[08:52] First, let's calculate the true positive rate. There are four true positives and
[08:56] rate. There are four true positives and there were zero false negatives.
[08:59] there were zero false negatives.
[09:00] there were zero false negatives. Doing the math gives us one.
[09:03] Doing the math gives us one. The true positive rate when the
[09:05] The true positive rate when the threshold is so low that every single
[09:08] threshold is so low that every single sample is classified as obese is one.
[09:12] sample is classified as obese is one. This means that every single obese
[09:14] This means that every single obese sample was correctly classified.
[09:18] sample was correctly classified. Now let's calculate the false positive
[09:20] Now let's calculate the false positive rate. There were four false positives in
[09:23] rate. There were four false positives in the confusion matrix and there were zero
[09:26] the confusion matrix and there were zero true negatives.
[09:28] true negatives. Doing the math gives us one. The false
[09:32] Doing the math gives us one. The false positive rate when the threshold is so
[09:34] positive rate when the threshold is so low that every single sample is
[09:36] low that every single sample is classified as obese is also one.
[09:40] classified as obese is also one. This means that every single sample that
[09:42] This means that every single sample that was not obese was incorrectly classified
[09:46] was not obese was incorrectly classified as obese.
[09:48] as obese. Now plot a point at 1 comma 1.
[09:52] Now plot a point at 1 comma 1. A point at 1 comma 1 means that even
[09:55] A point at 1 comma 1 means that even though we correctly classified all of
[09:57] though we correctly classified all of the obese samples, we incorrectly
[09:59] the obese samples, we incorrectly
[10:00] the obese samples, we incorrectly classified all of the samples that were
[10:02] classified all of the samples that were not obese.
[10:04] not obese. This green diagonal line shows where the
[10:07] This green diagonal line shows where the true positive rate equals the false
[10:09] true positive rate equals the false positive rate.
[10:11] positive rate. Any point on this line means that the
[10:13] Any point on this line means that the proportion of correctly classified obese
[10:16] proportion of correctly classified obese samples is the same as the proportion of
[10:18] samples is the same as the proportion of incorrectly classified samples that are
[10:21] incorrectly classified samples that are not obese.
[10:23] not obese. Going back to the logistic regression,
[10:25] Going back to the logistic regression, let's increase the threshold so that all
[10:27] let's increase the threshold so that all but the lightest sample are called
[10:29] but the lightest sample are called obese.
[10:32] obese. The new threshold gives us this
[10:33] The new threshold gives us this confusion matrix.
[10:36] confusion matrix. We then calculate the true positive rate
[10:38] We then calculate the true positive rate and the false positive rate and plot a
[10:42] and the false positive rate and plot a point at 0.75,
[10:44] point at 0.75, 1.
[10:46] 1. Since the new point is to the left of
[10:48] Since the new point is to the left of the dotted green line, we know that the
[10:51] the dotted green line, we know that the proportion of correctly classified
[10:53] proportion of correctly classified samples that were obese is greater than
[10:56] samples that were obese is greater than the proportion of samples that were
[10:57] the proportion of samples that were
[10:58] the proportion of samples that were incorrectly classified as obese.
[11:02] incorrectly classified as obese. In other words, the new threshold for
[11:04] In other words, the new threshold for deciding if a sample is obese or not is
[11:07] deciding if a sample is obese or not is better than the first one.
[11:10] better than the first one. Now, let's increase the threshold so
[11:12] Now, let's increase the threshold so that all but the two lightest samples
[11:14] that all but the two lightest samples are called obese.
[11:16] are called obese. The new threshold gives us this
[11:18] The new threshold gives us this confusion matrix.
[11:20] confusion matrix. We then calculate the true positive rate
[11:23] We then calculate the true positive rate and the false positive rate and plot a
[11:26] and the false positive rate and plot a point at 0.5,
[11:28] point at 0.5, 1.
[11:30] 1. The new point is even further to the
[11:32] The new point is even further to the left of the dotted green line, showing
[11:34] left of the dotted green line, showing that the new threshold further decreases
[11:37] that the new threshold further decreases the proportion of samples that were
[11:39] the proportion of samples that were incorrectly classified as obese.
[11:43] incorrectly classified as obese. In other words, the new threshold is the
[11:45] In other words, the new threshold is the best one so far.
[11:49] best one so far. Now we increase the threshold again,
[11:52] Now we increase the threshold again, create a confusion matrix,
[11:55] create a confusion matrix, calculate the true positive rate and the
[11:57] calculate the true positive rate and the false positive rate and plot the point.
[12:02] false positive rate and plot the point. Now we increase the threshold again,
[12:05] Now we increase the threshold again, create a confusion matrix,
[12:07] create a confusion matrix, calculate the true positive rate and the
[12:10] calculate the true positive rate and the false positive rate and plot the point.
[12:15] false positive rate and plot the point. The threshold represented by the new
[12:17] The threshold represented by the new point correctly classifies 75% of the
[12:20] point correctly classifies 75% of the obese samples and 100% of the samples
[12:23] obese samples and 100% of the samples that were not obese.
[12:26] that were not obese. In other words, this threshold resulted
[12:29] In other words, this threshold resulted in no false positives.
[12:32] in no false positives. Now we increase the threshold again and
[12:36] Now we increase the threshold again and plot the point. Now we increase the
[12:39] plot the point. Now we increase the threshold again and plot the point.
[12:43] threshold again and plot the point. Lastly, we choose a threshold that
[12:45] Lastly, we choose a threshold that classifies all of the samples as not
[12:48] classifies all of the samples as not obese
[12:49] obese
[12:50] obese and plot the point.
[12:52] and plot the point. The point at 0 comma 0 represents a
[12:55] The point at 0 comma 0 represents a threshold that results in zero true
[12:57] threshold that results in zero true positives and zero false positives.
[13:01] positives and zero false positives. If we want, we can connect the dots and
[13:05] If we want, we can connect the dots and that gives us an ROC graph.
[13:08] that gives us an ROC graph. The ROC graph summarizes all of the
[13:11] The ROC graph summarizes all of the confusion matrices that each threshold
[13:13] confusion matrices that each threshold
[13:14] confusion matrices that each threshold produced.
[13:15] produced. Without having to sort through the
[13:17] Without having to sort through the confusion matrices, I can tell that this
[13:19] confusion matrices, I can tell that this threshold is better than this threshold.
[13:24] threshold is better than this threshold. And depending on how many false
[13:26] And depending on how many false positives I'm willing to accept, the
[13:28] positives I'm willing to accept, the optimal threshold is either this one or
[13:31] optimal threshold is either this one or this one. Bam.
[13:35] this one. Bam. Now that we know what an ROC graph is,
[13:38] Now that we know what an ROC graph is, let's talk about the area under the
[13:40] let's talk about the area under the curve or AU.
[13:43] curve or AU. The AU is 0.9.
[13:47] The AU is 0.9. Bam.
[13:49] Bam. The AU makes it easy to compare one ROC
[13:52] The AU makes it easy to compare one ROC curve to another.
[13:55] curve to another. The AU for the red ROC curve is greater
[13:58] The AU for the red ROC curve is greater than the AU for the blue ROC curve,
[14:01] than the AU for the blue ROC curve, suggesting that the red curve is better.
[14:05] suggesting that the red curve is better. So if the red ROC curve represented
[14:07] So if the red ROC curve represented logistic regression and the blue ROC
[14:10] logistic regression and the blue ROC curve represented a random forest, you
[14:13] curve represented a random forest, you would use the logistic regression
[14:16] would use the logistic regression double bam.
[14:19] double bam. Now, one last thing before we're all
[14:21] Now, one last thing before we're all
[14:22] Now, one last thing before we're all done.
[14:23] done. Although ROC graphs are drawn using true
[14:26] Although ROC graphs are drawn using true positive rates and false positive rates
[14:29] positive rates and false positive rates to summarize confusion matrices, there
[14:31] to summarize confusion matrices, there are other metrics that attempt to do the
[14:33] are other metrics that attempt to do the
[14:34] are other metrics that attempt to do the same thing. For example, people often
[14:37] same thing. For example, people often replace the false positive rate with
[14:39] replace the false positive rate with precision.
[14:41] precision. Precision is the true positives divided
[14:44] Precision is the true positives divided by the sum of the true positives and
[14:47] by the sum of the true positives and false positives.
[14:49] false positives. Precision is the proportion of positive
[14:51] Precision is the proportion of positive results that were correctly classified.
[14:55] results that were correctly classified. If there were lots of samples that were
[14:57] If there were lots of samples that were not obese relative to the number of
[15:00] not obese relative to the number of obese samples, then precision might be
[15:02] obese samples, then precision might be more useful than the false positive
[15:04] more useful than the false positive rate.
[15:06] rate. This is because precision does not
[15:08] This is because precision does not include the number of true negatives in
[15:10] include the number of true negatives in its calculation and is not affected by
[15:12] its calculation and is not affected by the imbalance.
[15:15] the imbalance. In practice, this sort of imbalance
[15:17] In practice, this sort of imbalance occurs when studying a rare disease. In
[15:21] occurs when studying a rare disease. In this case, the study will contain many
[15:23] this case, the study will contain many more people without the disease than
[15:25] more people without the disease than with the disease. Bam.
[15:29] with the disease. Bam. In summary, ROC curves make it easy to
[15:33] In summary, ROC curves make it easy to identify the best threshold for making a
[15:36] identify the best threshold for making a decision. This threshold is better than
[15:39] decision. This threshold is better than
[15:40] decision. This threshold is better than this one.
[15:42] this one. and the AU can help you decide which
[15:44] and the AU can help you decide which categorization method is better. The red
[15:48] categorization method is better. The red method is better than the blue method.
[15:52] method is better than the blue method. Hooray! We've made it to the end of
[15:54] Hooray! We've made it to the end of another exciting Stack Quest. If you
[15:57] another exciting Stack Quest. If you like this Stat Quest and want to see
[15:58] like this Stat Quest and want to see more, please subscribe. And if you want
[16:01] more, please subscribe. And if you want to support Stat Quest, well, consider
[16:03] to support Stat Quest, well, consider getting a t-shirt or a hoodie or buying
[16:05] getting a t-shirt or a hoodie or buying one or two of my original songs. The
[16:07] one or two of my original songs. The
[16:08] one or two of my original songs. The links for doing that are below. All
[16:09] links for doing that are below. All
[16:10] links for doing that are below. All right, until next time. Quest on.

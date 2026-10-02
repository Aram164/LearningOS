---
video_id: g9c66TUylZ4
url: https://www.youtube.com/watch?v=g9c66TUylZ4
title: Regression Trees, Clearly Explained!!!
channel: StatQuest with Josh Starmer
duration: 22:33
language: en
unit: L12
status: OK
---

[00:00] Regression tree is for you and for me.
[00:07] Regression tree is for you and for me. StatQuest
[00:11] Hello, I'm Josh Starmer and welcome to StatQuest. Today we're going to talk
[00:15] StatQuest. Today we're going to talk about regression trees and they're going
[00:17] about regression trees and they're going to be clearly explained.
[00:20] to be clearly explained. This StatQuest assumes you are already
[00:22] This StatQuest assumes you are already familiar with the trade-off that plagues
[00:24] familiar with the trade-off that plagues all of machine learning, the
[00:26] all of machine learning, the bias-variance trade-off.
[00:29] bias-variance trade-off. And the basic ideas behind decision
[00:31] And the basic ideas behind decision trees.
[00:33] trees. And the basic ideas behind regression.
[00:36] And the basic ideas behind regression. If not, check out the quests. The links
[00:39] If not, check out the quests. The links are in the description below.
[00:41] are in the description below. Now, imagine we developed a new drug to
[00:44] Now, imagine we developed a new drug to cure the common cold.
[00:47] cure the common cold. However, we don't know the optimal
[00:49] However, we don't know the optimal dosage to give patients.
[00:52] dosage to give patients. So we do a clinical trial with different
[00:54] So we do a clinical trial with different dosages
[00:56] dosages and measure how effective each dosage
[00:58] and measure how effective each dosage is.
[01:00] is. If the data looked like this,
[01:03] If the data looked like this, and in general, the higher the dose,
[01:07] and in general, the higher the dose, the more effective the drug.
[01:10] the more effective the drug. Then we could easily fit a line to the
[01:12] Then we could easily fit a line to the data.
[01:14] data. And if someone told us they were taking
[01:16] And if someone told us they were taking a 27 mg dose,
[01:19] a 27 mg dose, we could use the line to predict that a
[01:21] we could use the line to predict that a 27 mg dose should be 62% effective.
[01:26] 27 mg dose should be 62% effective. However, what if the data looked like
[01:28] However, what if the data looked like this?
[01:30] this? Low dosages are not effective.
[01:34] Low dosages are not effective. Moderate dosages work really well.
[01:37] Moderate dosages work really well. Somewhat higher dosages work at about
[01:40] Somewhat higher dosages work at about 50% effectiveness.
[01:42] 50% effectiveness. And high dosages are not effective at
[01:45] And high dosages are not effective at all.
[01:46] all. In this case, fitting a straight line to
[01:49] In this case, fitting a straight line to the data will not be very useful.
[01:52] the data will not be very useful. For example, if someone told us they
[01:54] For example, if someone told us they were taking a 20 mg dose,
[01:58] were taking a 20 mg dose, then we would predict that a 20-mg dose
[02:01] then we would predict that a 20-mg dose should be 45% effective.
[02:04] should be 45% effective. Even though the observed data says it
[02:06] Even though the observed data says it should be 100% effective.
[02:10] should be 100% effective. So, we need to use something other than
[02:12] So, we need to use something other than a straight line to make predictions.
[02:15] a straight line to make predictions. One option is to use a regression tree.
[02:19] One option is to use a regression tree. Regression trees are a type of decision
[02:21] Regression trees are a type of decision tree.
[02:23] tree. In a regression tree, each leaf
[02:25] In a regression tree, each leaf represents a numeric value.
[02:28] represents a numeric value. In contrast, classification trees have
[02:31] In contrast, classification trees have true or false in their leaves
[02:35] true or false in their leaves or some other discrete category.
[02:38] or some other discrete category. With this regression tree, we start by
[02:41] With this regression tree, we start by asking if the dosage is less than 14.5.
[02:46] asking if the dosage is less than 14.5. If so, then we are talking about these
[02:49] If so, then we are talking about these six observations in the training data.
[02:52] six observations in the training data. And the average drug effectiveness for
[02:54] And the average drug effectiveness for these six observations is 4.2%.
[02:59] these six observations is 4.2%. So, the tree uses the average value,
[03:02] So, the tree uses the average value, 4.2%,
[03:03] 4.2%, as its prediction for people with
[03:05] as its prediction for people with dosages less than 14.5.
[03:09] On the other hand, if the dosage is
[03:12] On the other hand, if the dosage is greater than or equal to 14.5
[03:15] greater than or equal to 14.5 and greater than or equal to 29,
[03:19] and greater than or equal to 29, then we are talking about these four
[03:21] then we are talking about these four observations in the training data set.
[03:25] observations in the training data set. And the average drug effectiveness for
[03:27] And the average drug effectiveness for these four observations is 2.5%.
[03:31] these four observations is 2.5%. So, the tree uses the average value,
[03:34] So, the tree uses the average value, 2.5%,
[03:35] 2.5%, as its prediction for people with
[03:37] as its prediction for people with dosages greater than or equal to 29.
[03:41] dosages greater than or equal to 29. Now, if the dosage is greater than or
[03:44] Now, if the dosage is greater than or equal to 14.5
[03:46] equal to 14.5 and less than 29
[03:49] and less than 29 and greater than or equal to 23.5,
[03:53] and greater than or equal to 23.5, then we are talking about these five
[03:55] then we are talking about these five observations in the training data set.
[03:58] observations in the training data set. And the average drug effectiveness for
[04:00] And the average drug effectiveness for these five observations is 52.8%.
[04:05] So, the tree uses the average value,
[04:08] So, the tree uses the average value, 52.8%,
[04:10] 52.8%, as its prediction for people with
[04:11] as its prediction for people with dosages between 23.5
[04:14] dosages between 23.5 and 29.
[04:17] and 29. Lastly, if the dosage is greater than or
[04:20] Lastly, if the dosage is greater than or equal to 14.5
[04:22] equal to 14.5 and less than 29
[04:25] and less than 29 and less than 23.5,
[04:28] and less than 23.5, then we are talking about these four
[04:30] then we are talking about these four observations in the training data set.
[04:33] observations in the training data set. And the average drug effectiveness for
[04:35] And the average drug effectiveness for these four observations is 100%.
[04:39] these four observations is 100%. So, the tree uses the average value,
[04:42] So, the tree uses the average value, 100%, as its prediction for people with
[04:45] 100%, as its prediction for people with dosages between 14.5
[04:47] dosages between 14.5 and 23.5.
[04:51] Since each leaf corresponds to the average drug effectiveness in a
[04:55] average drug effectiveness in a different cluster of observations,
[04:58] different cluster of observations, the tree does a better job reflecting
[05:00] the tree does a better job reflecting the data than the straight line.
[05:04] the data than the straight line. At this point, you might be thinking,
[05:06] At this point, you might be thinking, "The regression tree is cool, but I can
[05:09] "The regression tree is cool, but I can also predict drug effectiveness just by
[05:11] also predict drug effectiveness just by looking at the graph."
[05:13] looking at the graph." For example, if someone said they were
[05:16] For example, if someone said they were taking a 27 mg dose,
[05:19] taking a 27 mg dose, then just by looking at the graph, I can
[05:22] then just by looking at the graph, I can tell that the drug will be about 50%
[05:24] tell that the drug will be about 50% effective.
[05:26] effective. So, why make a big deal about the
[05:28] So, why make a big deal about the regression tree?
[05:31] regression tree? When the data are super simple and we
[05:33] When the data are super simple and we are only using one predictor, dosage, to
[05:36] are only using one predictor, dosage, to predict drug effectiveness, making
[05:38] predict drug effectiveness, making predictions by eye isn't terrible.
[05:42] predictions by eye isn't terrible. But, when we have three or more
[05:43] But, when we have three or more predictors, like dosage, age, and sex,
[05:47] predictors, like dosage, age, and sex, to predict drug effectiveness, drawing a
[05:50] to predict drug effectiveness, drawing a graph is very difficult, if not
[05:52] graph is very difficult, if not impossible.
[05:54] impossible. In contrast, a regression tree easily
[05:57] In contrast, a regression tree easily accommodates the additional predictors.
[06:00] accommodates the additional predictors. For example, if we wanted to predict the
[06:03] For example, if we wanted to predict the drug effectiveness for this patient,
[06:06] drug effectiveness for this patient, we would start by asking if they are
[06:08] we would start by asking if they are older than 50.
[06:10] older than 50. And since they are not over 50, we
[06:13] And since they are not over 50, we follow the branch on the right and ask
[06:15] follow the branch on the right and ask if their dosage is greater than or equal
[06:17] if their dosage is greater than or equal to 29.
[06:19] to 29. And since their dosage is not greater
[06:22] And since their dosage is not greater than or equal to 29, we follow the
[06:24] than or equal to 29, we follow the branch on the right and ask if they are
[06:26] branch on the right and ask if they are female.
[06:28] female. And since they are female, we follow the
[06:31] And since they are female, we follow the branch on the left and predict that the
[06:33] branch on the left and predict that the dosage will be 100% effective.
[06:37] dosage will be 100% effective. And that's not too far off from the
[06:39] And that's not too far off from the truth, 98%.
[06:42] truth, 98%. Okay, now that we know that regression
[06:45] Okay, now that we know that regression trees can easily handle complicated
[06:47] trees can easily handle complicated data,
[06:49] data, let's go back to the original data with
[06:51] let's go back to the original data with just one predictor, dosage,
[06:54] just one predictor, dosage, and talk about how to build this
[06:56] and talk about how to build this regression tree from scratch.
[06:59] regression tree from scratch. And since regression trees are built
[07:01] And since regression trees are built from the top down,
[07:04] from the top down, the first thing we do is figure out why
[07:06] the first thing we do is figure out why we start by asking if dosage is less
[07:08] we start by asking if dosage is less than 14.5.
[07:11] than 14.5. Going back to the graph of the data,
[07:14] Going back to the graph of the data, let's focus on the two observations with
[07:17] let's focus on the two observations with the smallest dosages.
[07:20] the smallest dosages. Their average dosage is three, and that
[07:22] Their average dosage is three, and that corresponds to this dotted red line.
[07:26] corresponds to this dotted red line. Now we can build a very simple tree that
[07:28] Now we can build a very simple tree that splits the observations into two groups
[07:31] splits the observations into two groups based on whether or not dosage is less
[07:33] based on whether or not dosage is less than three.
[07:36] than three. The point on the far left is the only
[07:38] The point on the far left is the only one with dosage less than three.
[07:42] one with dosage less than three. And the average drug effectiveness for
[07:44] And the average drug effectiveness for that one point is zero.
[07:47] that one point is zero. So, we put zero in the leaf on the left
[07:49] So, we put zero in the leaf on the left side for when dosage is less than three.
[07:53] side for when dosage is less than three. All of the other points have dosages
[07:56] All of the other points have dosages greater than or equal to three.
[07:59] greater than or equal to three. And the average drug effectiveness for
[08:01] And the average drug effectiveness for all of the points with dosages greater
[08:03] all of the points with dosages greater than or equal to three is 38.8.
[08:08] So, we put 38.8 in the leaf on the right
[08:11] So, we put 38.8 in the leaf on the right side for when dosage is greater than or
[08:14] side for when dosage is greater than or equal to three.
[08:16] equal to three. The values in each leaf are the
[08:18] The values in each leaf are the predictions that this simple tree will
[08:20] predictions that this simple tree will make for drug effectiveness.
[08:23] make for drug effectiveness. For example, this point on the far left
[08:26] For example, this point on the far left has dosage less than three.
[08:29] has dosage less than three. And the tree predicts that the drug
[08:31] And the tree predicts that the drug effectiveness will be zero.
[08:34] effectiveness will be zero. The prediction for this point, drug
[08:36] The prediction for this point, drug effectiveness equals zero, is pretty
[08:39] effectiveness equals zero, is pretty good since it is the same as the
[08:41] good since it is the same as the observed value.
[08:44] observed value. In contrast, for this point, which has
[08:46] In contrast, for this point, which has dosage greater than three,
[08:49] dosage greater than three, the tree predicts that the drug
[08:51] the tree predicts that the drug effectiveness will be 38.8.
[08:55] And that prediction is not very good since the observed drug effectiveness is
[09:00] since the observed drug effectiveness is 100%.
[09:02] 100%. Note, we can visualize how bad the
[09:05] Note, we can visualize how bad the prediction is by drawing a dotted line
[09:07] prediction is by drawing a dotted line between the observed and predicted
[09:09] between the observed and predicted values.
[09:11] values. In other words, the dotted line is a
[09:13] In other words, the dotted line is a residual.
[09:15] residual. For each point in the data, we can draw
[09:18] For each point in the data, we can draw its residual, the difference between the
[09:20] its residual, the difference between the observed and predicted values,
[09:23] observed and predicted values, and we can use the residuals to quantify
[09:26] and we can use the residuals to quantify the quality of these predictions.
[09:30] the quality of these predictions. Starting with the only point with dosage
[09:32] Starting with the only point with dosage less than three,
[09:34] less than three, we calculate the difference between its
[09:36] we calculate the difference between its observed drug effectiveness, zero,
[09:40] observed drug effectiveness, zero, and the predicted drug effectiveness,
[09:42] and the predicted drug effectiveness, zero,
[09:44] zero, and then square the difference.
[09:47] and then square the difference. In other words, this is the squared
[09:49] In other words, this is the squared residual for the first point.
[09:53] residual for the first point. Now we add the square residuals for the
[09:55] Now we add the square residuals for the remaining points with dosages greater
[09:58] remaining points with dosages greater than or equal to three.
[10:01] than or equal to three. In other words, for this point,
[10:04] In other words, for this point, we calculate the difference between the
[10:06] we calculate the difference between the observed and predicted values
[10:09] observed and predicted values and square it,
[10:11] and square it, and then add it to the first term.
[10:14] and then add it to the first term. Then we do the same thing for the next
[10:16] Then we do the same thing for the next point,
[10:18] point, and the next point,
[10:20] and the next point, and the rest of the points,
[10:28] until we have added squared residuals for every point.
[10:33] for every point. Thus, to evaluate the predictions made
[10:35] Thus, to evaluate the predictions made when the threshold is dosage less than
[10:38] when the threshold is dosage less than three,
[10:40] three, we add up the squared residuals for
[10:41] we add up the squared residuals for every point
[10:43] every point and get 27,468.5.
[10:49] Note, we can plot the sum of squared
[10:52] Note, we can plot the sum of squared residuals on this graph.
[10:55] residuals on this graph. The Y axis corresponds to the sum of
[10:57] The Y axis corresponds to the sum of squared residuals.
[11:00] squared residuals. And the X axis corresponds to dosage
[11:03] And the X axis corresponds to dosage thresholds.
[11:05] thresholds. In this case, the dosage threshold was
[11:08] In this case, the dosage threshold was three.
[11:10] three. But if we focus on the next two points
[11:12] But if we focus on the next two points in the graph
[11:14] in the graph and calculate their average dosage,
[11:16] and calculate their average dosage, which is five,
[11:18] which is five, then we can use dosage less than five as
[11:21] then we can use dosage less than five as a new threshold.
[11:23] a new threshold. And using dosage less than five gives us
[11:26] And using dosage less than five gives us new predictions
[11:28] new predictions and new residuals.
[11:30] and new residuals. And that means we can add a new sum of
[11:32] And that means we can add a new sum of squared residuals to our graph.
[11:36] squared residuals to our graph. In this case, the new threshold, dosage
[11:39] In this case, the new threshold, dosage less than five, results in a smaller sum
[11:42] less than five, results in a smaller sum of squared residuals.
[11:44] of squared residuals. And that means using dosage less than
[11:46] And that means using dosage less than five as the threshold resulted in better
[11:49] five as the threshold resulted in better predictions overall.
[11:52] predictions overall. Bam!
[11:54] Bam! Now let's focus on the next two points.
[11:58] Now let's focus on the next two points. Calculate their average, which is seven,
[12:02] Calculate their average, which is seven, and use dosage less than seven as a new
[12:05] and use dosage less than seven as a new threshold.
[12:07] threshold. Again, the new threshold gives us new
[12:10] Again, the new threshold gives us new predictions,
[12:12] predictions, new residuals,
[12:15] new residuals, and a new sum of squared residuals.
[12:18] and a new sum of squared residuals. Now shift the threshold over to the
[12:20] Now shift the threshold over to the average dosage for the next two points,
[12:24] average dosage for the next two points, and add a new sum of squared residuals
[12:26] and add a new sum of squared residuals to the graph.
[12:29] to the graph. And we repeat until we have calculated
[12:31] And we repeat until we have calculated the sum of squared residuals for all of
[12:33] the sum of squared residuals for all of the remaining thresholds.
[12:39] Bam! Now we can see the sum of squared
[12:42] Now we can see the sum of squared residuals for all of the thresholds.
[12:46] residuals for all of the thresholds. And dosage less than 14.5
[12:48] And dosage less than 14.5 has the smallest sum of squared
[12:50] has the smallest sum of squared residuals.
[12:52] residuals. So dosage less than 14.5
[12:55] So dosage less than 14.5 will be the root of the tree.
[12:58] will be the root of the tree. In summary, we split the data into two
[13:01] In summary, we split the data into two groups by finding the threshold that
[13:03] groups by finding the threshold that gave us the smallest sum of squared
[13:05] gave us the smallest sum of squared residuals.
[13:07] residuals. Bam!
[13:11] Now let's focus on the six observations with dosage less than 14.5
[13:16] with dosage less than 14.5 that ended up in the node to the left of
[13:18] that ended up in the node to the left of the root.
[13:20] the root. In theory, we could split these six
[13:22] In theory, we could split these six observations into two smaller groups
[13:25] observations into two smaller groups just like we did before.
[13:27] just like we did before. By calculating the sum of squared
[13:29] By calculating the sum of squared residuals for different thresholds
[13:32] residuals for different thresholds and choosing the threshold with the
[13:34] and choosing the threshold with the lowest sum of squared residuals.
[13:38] Note, this observation
[13:41] Note, this observation has dosage less than 14.5
[13:44] has dosage less than 14.5 and does not have dosage less than 11.5,
[13:48] and does not have dosage less than 11.5, so it is the only observation to end up
[13:51] so it is the only observation to end up in this node.
[13:53] in this node. And since we can't split a single
[13:55] And since we can't split a single observation into two groups, we will
[13:57] observation into two groups, we will call this node a leaf.
[14:00] call this node a leaf. However, since the remaining five
[14:02] However, since the remaining five observations go to the other node, we
[14:05] observations go to the other node, we can split them once more.
[14:08] can split them once more. Now we have divided the observations
[14:10] Now we have divided the observations with dosage less than 14.5
[14:13] with dosage less than 14.5 into three separate groups.
[14:16] into three separate groups. These two leaves only contain one
[14:18] These two leaves only contain one observation each and cannot be split
[14:21] observation each and cannot be split into smaller groups.
[14:24] into smaller groups. In contrast, this leaf contains four
[14:27] In contrast, this leaf contains four observations.
[14:29] observations. That said, those four observations all
[14:32] That said, those four observations all have the same drug effectiveness, so we
[14:34] have the same drug effectiveness, so we don't need to split them into smaller
[14:36] don't need to split them into smaller groups.
[14:38] groups. So we are done splitting the
[14:40] So we are done splitting the observations with dosage less than 14.5
[14:44] observations with dosage less than 14.5 into smaller groups.
[14:46] into smaller groups. Note, the predictions that this tree
[14:49] Note, the predictions that this tree makes for all observations with dosage
[14:52] makes for all observations with dosage less than 14.5
[14:54] less than 14.5 are perfect.
[14:56] are perfect. In other words, this observation has 20%
[15:00] In other words, this observation has 20% drug effectiveness
[15:02] drug effectiveness and the tree predicts 20% drug
[15:04] and the tree predicts 20% drug effectiveness.
[15:06] effectiveness. So the observed and predicted values are
[15:09] So the observed and predicted values are the same.
[15:11] the same. This observation has 5% drug
[15:13] This observation has 5% drug effectiveness
[15:15] effectiveness and that's exactly what the tree
[15:16] and that's exactly what the tree predicts.
[15:18] predicts. These four observations all have 0% drug
[15:22] These four observations all have 0% drug effectiveness.
[15:24] effectiveness. And that's exactly what the tree
[15:25] And that's exactly what the tree predicts.
[15:28] predicts. Is that awesome?
[15:30] Is that awesome? No.
[15:31] No. When a model fits the training data
[15:33] When a model fits the training data perfectly, it probably means it is
[15:36] perfectly, it probably means it is overfit and will not perform well with
[15:38] overfit and will not perform well with new data.
[15:40] new data. In machine learning lingo, the model has
[15:43] In machine learning lingo, the model has no bias, but potentially large variance.
[15:47] no bias, but potentially large variance. Bummer.
[15:49] Bummer. Is there a way to prevent our tree from
[15:51] Is there a way to prevent our tree from overfitting the training data?
[15:54] overfitting the training data? Yes. There are a bunch of techniques.
[15:58] Yes. There are a bunch of techniques. The simplest is to only split
[16:00] The simplest is to only split observations when there are more than
[16:02] observations when there are more than some minimum number.
[16:04] some minimum number. Typically, the minimum number of
[16:06] Typically, the minimum number of observations to allow for a split is 20.
[16:10] observations to allow for a split is 20. However, since this example doesn't have
[16:13] However, since this example doesn't have many observations, I set the minimum to
[16:15] many observations, I set the minimum to seven.
[16:17] seven. In other words, since there are only six
[16:20] In other words, since there are only six observations with dosage less than 14.5,
[16:25] observations with dosage less than 14.5, we will not split the observations in
[16:27] we will not split the observations in this node.
[16:29] this node. Instead, this node will become a leaf.
[16:33] Instead, this node will become a leaf. And the output will be the average drug
[16:35] And the output will be the average drug effectiveness for the six observations
[16:38] effectiveness for the six observations with dosage less than 14.5,
[16:41] with dosage less than 14.5, 4.2%.
[16:43] 4.2%. Bam!
[16:46] Bam! Now we need to figure out what to do
[16:48] Now we need to figure out what to do with the remaining 13 observations with
[16:51] with the remaining 13 observations with dosages greater than or equal to 14.5.
[16:55] dosages greater than or equal to 14.5. Since we have more than seven
[16:57] Since we have more than seven observations on the right side, we can
[17:00] observations on the right side, we can split them into two groups.
[17:03] split them into two groups. And we do that by finding the threshold
[17:05] And we do that by finding the threshold that gives us the smallest sum of
[17:07] that gives us the smallest sum of squared residuals.
[17:10] squared residuals. Note, there are only four observations
[17:12] Note, there are only four observations with dosage greater than or equal to 29.
[17:16] with dosage greater than or equal to 29. Thus, there are only four observations
[17:19] Thus, there are only four observations in this node.
[17:21] in this node. Thus, we will make this a leaf because
[17:24] Thus, we will make this a leaf because it contains fewer than seven
[17:26] it contains fewer than seven observations.
[17:28] observations. And the average drug effectiveness for
[17:31] And the average drug effectiveness for these four observations 2.5%.
[17:35] these four observations 2.5%. Now we need to figure out what to do
[17:37] Now we need to figure out what to do with the nine observations with dosages
[17:40] with the nine observations with dosages between 14.5
[17:42] between 14.5 and 29.
[17:44] and 29. Since we have more than seven
[17:45] Since we have more than seven observations, we can split them into two
[17:48] observations, we can split them into two groups
[17:49] groups by finding the threshold that gives us
[17:51] by finding the threshold that gives us the minimum sum of squared residuals.
[17:55] the minimum sum of squared residuals. Note, since there are fewer than seven
[17:57] Note, since there are fewer than seven observations in each of these two
[17:59] observations in each of these two groups,
[18:01] groups, this is the last split because none of
[18:03] this is the last split because none of the leaves have more than seven
[18:05] the leaves have more than seven observations in them.
[18:08] observations in them. So we use the average drug effectiveness
[18:10] So we use the average drug effectiveness for the observations with dosages
[18:12] for the observations with dosages between 14.5
[18:14] between 14.5 and 23.5
[18:16] and 23.5 100% as the output for the leaf on the
[18:19] 100% as the output for the leaf on the right.
[18:21] right. And we use the average drug
[18:23] And we use the average drug effectiveness for observations with
[18:25] effectiveness for observations with dosages between 23.5 and 29 52.8%
[18:30] dosages between 23.5 and 29 52.8% as the output for the leaf on the left.
[18:34] as the output for the leaf on the left. Since no leaf has more than seven
[18:36] Since no leaf has more than seven observations in it,
[18:38] observations in it, we're done building the tree.
[18:41] we're done building the tree. And each leaf corresponds to the average
[18:43] And each leaf corresponds to the average drug effectiveness from a different
[18:45] drug effectiveness from a different cluster of observations.
[18:48] cluster of observations. Double bam.
[18:52] Double bam. So far, we have built a tree using a
[18:54] So far, we have built a tree using a single predictor, dosage, to predict
[18:57] single predictor, dosage, to predict drug effectiveness.
[19:00] drug effectiveness. Now let's talk about how to build a tree
[19:02] Now let's talk about how to build a tree to predict drug effectiveness using a
[19:04] to predict drug effectiveness using a bunch of predictors.
[19:06] bunch of predictors. Just like before, we will start by using
[19:09] Just like before, we will start by using dosage to predict drug effectiveness.
[19:13] dosage to predict drug effectiveness. Thus, just like before, we will try
[19:16] Thus, just like before, we will try different thresholds for dosage and
[19:18] different thresholds for dosage and calculate the sum of squared residuals
[19:20] calculate the sum of squared residuals at each step
[19:22] at each step and pick the threshold that gives us the
[19:24] and pick the threshold that gives us the minimum sum of squared residuals.
[19:27] minimum sum of squared residuals. The best threshold becomes a candidate
[19:30] The best threshold becomes a candidate for the root.
[19:32] for the root. Now we focus on using age to predict
[19:35] Now we focus on using age to predict drug effectiveness.
[19:38] drug effectiveness. Just like with dosage, we try different
[19:40] Just like with dosage, we try different thresholds for age and calculate the sum
[19:42] thresholds for age and calculate the sum of squared residuals at each step
[19:45] of squared residuals at each step and pick the one that gives us the
[19:47] and pick the one that gives us the minimum sum of squared residuals.
[19:50] minimum sum of squared residuals. The best threshold becomes another
[19:52] The best threshold becomes another candidate for the root.
[19:55] candidate for the root. Now we focus on using sex to predict
[19:58] Now we focus on using sex to predict drug effectiveness.
[20:00] drug effectiveness. With sex, there is only one threshold to
[20:03] With sex, there is only one threshold to try.
[20:05] try. So, we use that threshold to calculate
[20:07] So, we use that threshold to calculate the sum of squared residuals
[20:10] the sum of squared residuals and that becomes another candidate for
[20:11] and that becomes another candidate for the root.
[20:14] the root. Now we compare the sum of squared
[20:15] Now we compare the sum of squared residuals, SSRs, for each candidate
[20:20] residuals, SSRs, for each candidate and pick the candidate with the lowest
[20:22] and pick the candidate with the lowest value.
[20:24] value. Since age greater than 50 had the lowest
[20:27] Since age greater than 50 had the lowest sum of squared residuals, it becomes the
[20:29] sum of squared residuals, it becomes the root of the tree.
[20:31] root of the tree. Then we grow the tree just like before,
[20:34] Then we grow the tree just like before, except now we compare the lowest sum of
[20:36] except now we compare the lowest sum of squared residuals from each predictor.
[20:39] squared residuals from each predictor. And just like before, when a leaf has
[20:41] And just like before, when a leaf has less than a minimum number of
[20:43] less than a minimum number of observations, which is usually 20, but
[20:46] observations, which is usually 20, but we are using seven, we stop trying to
[20:48] we are using seven, we stop trying to divide them.
[20:51] divide them. Triple bam!
[20:54] Triple bam! In summary,
[20:56] In summary, regression trees are a type of decision
[20:58] regression trees are a type of decision tree.
[21:00] tree. In a regression tree, each leaf
[21:02] In a regression tree, each leaf represents a numeric value.
[21:06] represents a numeric value. We determine how to divide the
[21:08] We determine how to divide the observations by trying different
[21:09] observations by trying different thresholds and calculating the sum of
[21:11] thresholds and calculating the sum of squared residuals at each step.
[21:14] squared residuals at each step. Beep boop boop beep beep
[21:16] Beep boop boop beep beep Beep boop boop beep beep boop boop beep
[21:18] Beep boop boop beep beep boop boop beep The threshold with the smallest sum of
[21:21] The threshold with the smallest sum of squared residuals
[21:23] squared residuals becomes a candidate for the root of the
[21:24] becomes a candidate for the root of the tree.
[21:26] tree. If we have more than one predictor, we
[21:29] If we have more than one predictor, we find the optimal threshold for each one
[21:32] find the optimal threshold for each one and pick the candidate with the smallest
[21:34] and pick the candidate with the smallest sum of squared residuals
[21:36] sum of squared residuals to be the root.
[21:38] to be the root. When we have fewer than some minimum
[21:40] When we have fewer than some minimum number of observations in a node, seven
[21:43] number of observations in a node, seven in this example, but more commonly 20,
[21:46] in this example, but more commonly 20, then that node becomes a leaf.
[21:50] then that node becomes a leaf. Otherwise, we repeat the process to
[21:52] Otherwise, we repeat the process to split the remaining observations
[21:55] split the remaining observations until we can no longer split the
[21:57] until we can no longer split the observations into smaller groups.
[22:01] observations into smaller groups. And then we are done.
[22:03] And then we are done. Hooray! We've made it to the end of
[22:06] Hooray! We've made it to the end of another exciting StatQuest. If you like
[22:08] another exciting StatQuest. If you like this StatQuest and want to see more,
[22:10] this StatQuest and want to see more, please subscribe. And if you want to
[22:12] please subscribe. And if you want to support StatQuest, consider contributing
[22:14] support StatQuest, consider contributing to my Patreon campaign, buying one or
[22:17] to my Patreon campaign, buying one or two of my original songs or a t-shirt or
[22:19] two of my original songs or a t-shirt or a hoodie, or just donate. The links are
[22:22] a hoodie, or just donate. The links are in the description below. All right,
[22:24] in the description below. All right, until next time, quest on.

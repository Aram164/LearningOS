---
video_id: Kdsp6soqA7o
url: https://www.youtube.com/watch?v=Kdsp6soqA7o
title: Machine Learning Fundamentals: The Confusion Matrix
channel: StatQuest with Josh Starmer
duration: 7:12
language: en
unit: L01
status: OK
---

[00:01] If you feel confused,
[00:05] don't sweat it. StatQuest is here.
[00:12] StatQuest. Hello, I'm Josh Starmer and welcome to
[00:17] Hello, I'm Josh Starmer and welcome to StatQuest. Today we're going to cover
[00:19] StatQuest. Today we're going to cover another machine learning fundamental,
[00:21] another machine learning fundamental, the confusion matrix, and it's going to
[00:23] the confusion matrix, and it's going to be clearly explained.
[00:26] be clearly explained. Imagine that we have this medical data.
[00:29] Imagine that we have this medical data. We've got some clinical measurements
[00:31] We've got some clinical measurements like chest pain, good blood circulation,
[00:33] like chest pain, good blood circulation, blocked arteries, and weight.
[00:36] blocked arteries, and weight. And we want to apply a machine learning
[00:38] And we want to apply a machine learning method to them to predict whether or not
[00:40] method to them to predict whether or not someone will develop heart disease.
[00:43] someone will develop heart disease. To do this, we could use logistic
[00:45] To do this, we could use logistic regression
[00:47] regression or K nearest neighbors
[00:49] or K nearest neighbors or random forest
[00:51] or random forest or some other method. There are tons to
[00:54] or some other method. There are tons to choose from.
[00:55] choose from. How do we decide which one works best
[00:58] How do we decide which one works best with our data?
[01:00] with our data? We start by dividing the data into
[01:02] We start by dividing the data into training and testing sets.
[01:05] training and testing sets. Note, this would be an excellent
[01:08] Note, this would be an excellent opportunity to use cross-validation. And
[01:10] opportunity to use cross-validation. And if you're not familiar with that, well,
[01:12] if you're not familiar with that, well, check out the StatQuest.
[01:15] check out the StatQuest. Then we train all of the methods we're
[01:17] Then we train all of the methods we're interested in with the training data.
[01:21] interested in with the training data. And then test each method on the testing
[01:23] And then test each method on the testing set.
[01:26] set. Now we need to summarize how each method
[01:28] Now we need to summarize how each method performed on the testing data.
[01:32] performed on the testing data. One way to do this is by creating a
[01:34] One way to do this is by creating a confusion matrix for each method.
[01:38] confusion matrix for each method. The rows in a confusion matrix
[01:40] The rows in a confusion matrix correspond to what the machine learning
[01:42] correspond to what the machine learning algorithm predicted.
[01:44] algorithm predicted. And the columns correspond to the known
[01:47] And the columns correspond to the known truth.
[01:49] truth. Since there are only two categories to
[01:51] Since there are only two categories to choose from,
[01:52] choose from, heart disease or does not have heart
[01:56] heart disease or does not have heart disease,
[01:58] disease, then the top left corner contains true
[02:01] then the top left corner contains true positives.
[02:03] positives. These are patients that had heart
[02:05] These are patients that had heart disease that were correctly identified
[02:08] disease that were correctly identified by the algorithm.
[02:10] by the algorithm. The true negatives are in the bottom
[02:12] The true negatives are in the bottom right-hand corner.
[02:14] right-hand corner. These are patients that did not have
[02:16] These are patients that did not have heart disease that were correctly
[02:18] heart disease that were correctly identified by the algorithm.
[02:21] identified by the algorithm. The bottom left-hand corner contains
[02:23] The bottom left-hand corner contains false negatives.
[02:25] false negatives. False negatives are when a patient has
[02:28] False negatives are when a patient has heart disease, but the algorithm said
[02:30] heart disease, but the algorithm said they didn't.
[02:32] they didn't. Lastly, the top right-hand corner
[02:34] Lastly, the top right-hand corner contains false positives.
[02:37] contains false positives. False positives are patients that do not
[02:39] False positives are patients that do not have heart disease, but the algorithm
[02:42] have heart disease, but the algorithm says they do.
[02:44] says they do. For example, when we applied the random
[02:46] For example, when we applied the random forest to the testing data,
[02:49] forest to the testing data, there were 142 true positives, patients
[02:53] there were 142 true positives, patients with heart disease that were correctly
[02:55] with heart disease that were correctly classified,
[02:57] classified, and 110 true negatives, patients without
[03:00] and 110 true negatives, patients without heart disease that were correctly
[03:02] heart disease that were correctly classified.
[03:04] classified. However, the algorithm misclassified 29
[03:08] However, the algorithm misclassified 29 patients that did have heart disease by
[03:10] patients that did have heart disease by saying they did not. These are false
[03:13] saying they did not. These are false negatives.
[03:15] negatives. And the algorithm misclassified 22
[03:17] And the algorithm misclassified 22 patients that did not have heart disease
[03:20] patients that did not have heart disease by saying that they did. These are false
[03:22] by saying that they did. These are false positives.
[03:25] positives. The numbers along the diagonal, the
[03:27] The numbers along the diagonal, the green boxes, tell us how many times the
[03:30] green boxes, tell us how many times the samples were correctly classified.
[03:33] samples were correctly classified. The numbers not on the diagonal, the red
[03:36] The numbers not on the diagonal, the red boxes, are samples that the algorithm
[03:39] boxes, are samples that the algorithm messed up.
[03:41] messed up. Now we can compare the random forest
[03:43] Now we can compare the random forest confusion matrix
[03:46] confusion matrix to the confusion matrix we get when we
[03:48] to the confusion matrix we get when we use K nearest neighbors.
[03:51] use K nearest neighbors. K nearest neighbors was worse the random
[03:54] K nearest neighbors was worse the random forest at predicting patients with the
[03:56] forest at predicting patients with the heart disease,
[03:58] heart disease, 107 versus 142,
[04:02] 107 versus 142, and worse at predicting patients without
[04:05] and worse at predicting patients without heart disease, 79 versus 110.
[04:10] heart disease, 79 versus 110. So, if we had to choose between using
[04:11] So, if we had to choose between using the random forest and K-nearest
[04:13] the random forest and K-nearest neighbors, we would choose the random
[04:16] neighbors, we would choose the random forest.
[04:18] forest. Bam!
[04:20] Bam! Lastly, we can apply logistic regression
[04:22] Lastly, we can apply logistic regression to the testing data set and create a
[04:24] to the testing data set and create a confusion matrix.
[04:27] confusion matrix. These two confusion matrices are very
[04:29] These two confusion matrices are very similar and make it hard to choose which
[04:32] similar and make it hard to choose which machine learning method is a better fit
[04:34] machine learning method is a better fit for this data.
[04:36] for this data. We'll talk about more sophisticated
[04:38] We'll talk about more sophisticated metrics like sensitivity, specificity,
[04:41] metrics like sensitivity, specificity, ROC, and AOC that can help us make a
[04:44] ROC, and AOC that can help us make a decision in the next Stack Quests.
[04:48] decision in the next Stack Quests. Now that we have the basic confusion
[04:50] Now that we have the basic confusion matrix figured out, let's look at a more
[04:52] matrix figured out, let's look at a more complicated one.
[04:55] complicated one. Here's a new data set.
[04:57] Here's a new data set. Now the question is, based on what
[05:00] Now the question is, based on what people think of these movies, Jurassic
[05:02] people think of these movies, Jurassic Park III, Run for Your Wife, Out Cold,
[05:06] Park III, Run for Your Wife, Out Cold, spelled with a K, and Howard the Duck,
[05:09] spelled with a K, and Howard the Duck, can we use a machine learning method to
[05:11] can we use a machine learning method to predict their favorite movie?
[05:14] predict their favorite movie? If the only options for favorite movie
[05:17] If the only options for favorite movie were Troll 2, Gore Police, or Cool as
[05:21] were Troll 2, Gore Police, or Cool as Ice,
[05:23] Ice, then the confusion matrix would have
[05:24] then the confusion matrix would have three rows and three columns.
[05:28] three rows and three columns. But just like before, the diagonal, the
[05:31] But just like before, the diagonal, the green boxes, are where the machine
[05:33] green boxes, are where the machine learning algorithm did the right thing,
[05:36] learning algorithm did the right thing, and everything else is where the
[05:38] and everything else is where the algorithm messed up.
[05:40] algorithm messed up. In this case, the machine learning
[05:42] In this case, the machine learning algorithm didn't do very well, but can
[05:45] algorithm didn't do very well, but can you blame it? These are all terrible
[05:47] you blame it? These are all terrible movies.
[05:49] movies. Bam!
[05:51] Bam! Ultimately, the size of the confusion
[05:53] Ultimately, the size of the confusion matrix is determined by the number of
[05:55] matrix is determined by the number of things we want to predict.
[05:58] things we want to predict. In the first example, we were only
[06:00] In the first example, we were only trying to predict two things, if someone
[06:02] trying to predict two things, if someone had heart disease or if they didn't.
[06:05] had heart disease or if they didn't. And that gave us a confusion matrix with
[06:08] And that gave us a confusion matrix with two rows and two columns.
[06:11] two rows and two columns. In the second example, we had three
[06:13] In the second example, we had three things to choose from.
[06:15] things to choose from. And a confusion matrix with three rows
[06:18] And a confusion matrix with three rows and three columns.
[06:20] and three columns. If we had four things to choose from, we
[06:23] If we had four things to choose from, we get a confusion matrix with four rows
[06:25] get a confusion matrix with four rows and four columns.
[06:28] and four columns. And if we had 40 things to choose from,
[06:30] And if we had 40 things to choose from, we get a confusion matrix with 40 rows
[06:33] we get a confusion matrix with 40 rows and 40 columns.
[06:35] and 40 columns. Double bam!
[06:38] Double bam! In summary, a confusion matrix tells you
[06:41] In summary, a confusion matrix tells you what your machine learning algorithm did
[06:43] what your machine learning algorithm did right
[06:44] right and what it did wrong.
[06:47] and what it did wrong. Hooray! We've made it to the end of
[06:49] Hooray! We've made it to the end of another exciting StatQuest. If you like
[06:52] another exciting StatQuest. If you like this StatQuest and want to see more,
[06:54] this StatQuest and want to see more, please subscribe. And if you want to
[06:55] please subscribe. And if you want to support StatQuest, well, consider buying
[06:58] support StatQuest, well, consider buying one or two of my original songs. All
[07:01] one or two of my original songs. All right, until next time, quest on.

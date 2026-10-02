---
video_id: vMh0zPT0tLI
url: https://www.youtube.com/watch?v=vMh0zPT0tLI
title: Stochastic Gradient Descent, Clearly Explained!!!
channel: StatQuest with Josh Starmer
duration: 10:53
language: en
unit: L15
status: OK
---

[00:00] Going to do something crazy? Going to do something random?
[00:05] Going to do something random? It's got to be stochastic.
[00:07] It's got to be stochastic. It's got to be
[00:09] It's got to be StatQuest.
[00:13] Hello, I'm Josh Starmer and welcome to StatQuest. Today we're going to talk
[00:17] StatQuest. Today we're going to talk about stochastic gradient descent and
[00:19] about stochastic gradient descent and it's going to be clearly explained.
[00:22] it's going to be clearly explained. Note, this StatQuest assumes that you
[00:25] Note, this StatQuest assumes that you are already familiar with gradient
[00:26] are already familiar with gradient descent. If not, check out the quest.
[00:29] descent. If not, check out the quest. The link is in the description below.
[00:32] The link is in the description below. This video picks up where the original
[00:34] This video picks up where the original leaves off providing more details about
[00:37] leaves off providing more details about how stochastic gradient descent works
[00:39] how stochastic gradient descent works and some of its more subtle advantages.
[00:42] and some of its more subtle advantages. Now, even though I just said you need to
[00:45] Now, even though I just said you need to watch the StatQuest on gradient descent,
[00:47] watch the StatQuest on gradient descent, let's do a little review to demonstrate
[00:49] let's do a little review to demonstrate the problem that stochastic gradient
[00:51] the problem that stochastic gradient descent solves.
[00:53] descent solves. In the StatQuest on gradient descent, we
[00:55] In the StatQuest on gradient descent, we took this simple data set,
[00:57] took this simple data set, height and weight measurements from
[00:59] height and weight measurements from three different people,
[01:01] three different people, and we wanted to fit a line to it using
[01:03] and we wanted to fit a line to it using gradient descent.
[01:05] gradient descent. However, at first we started out with
[01:08] However, at first we started out with this generic equation for a line.
[01:11] this generic equation for a line. And the goal was to find the optimal
[01:13] And the goal was to find the optimal values for the intercept and the slope.
[01:16] values for the intercept and the slope. For example, if we started with the
[01:18] For example, if we started with the intercept equals zero and the slope
[01:21] intercept equals zero and the slope equals one,
[01:23] equals one, then we could use weight
[01:25] then we could use weight to predict height.
[01:27] to predict height. Then we would use the sum of the squared
[01:29] Then we would use the sum of the squared residuals as the loss function to
[01:32] residuals as the loss function to determine how well the initial line fit
[01:34] determine how well the initial line fit the data.
[01:36] the data. Note, the sum of the squared residuals
[01:38] Note, the sum of the squared residuals is just one of many different loss
[01:40] is just one of many different loss functions that can evaluate how well
[01:42] functions that can evaluate how well something fits the data.
[01:45] something fits the data. In this case, that something is a line.
[01:49] In this case, that something is a line. To find the optimal values for the
[01:51] To find the optimal values for the intercept and slope, we plug the
[01:53] intercept and slope, we plug the equation for the predicted height into
[01:56] equation for the predicted height into the sum of the squared residuals.
[01:59] the sum of the squared residuals. Then we took the derivative of the sum
[02:00] Then we took the derivative of the sum of the squared residuals with respect to
[02:02] of the squared residuals with respect to the intercept
[02:04] the intercept and with respect to the slope.
[02:07] and with respect to the slope. Then we plugged in the values from the
[02:09] Then we plugged in the values from the observed data into the derivative with
[02:12] observed data into the derivative with respect to the intercept.
[02:14] respect to the intercept. And then we did the same thing for the
[02:16] And then we did the same thing for the derivative with respect to the slope.
[02:19] derivative with respect to the slope. Then we plugged in the initial guess for
[02:21] Then we plugged in the initial guess for the intercept, zero,
[02:24] the intercept, zero, and the initial guess for the slope,
[02:26] and the initial guess for the slope, one.
[02:28] one. We did the math,
[02:29] We did the math, plugged the slopes into the step size
[02:32] plugged the slopes into the step size formulas,
[02:33] formulas, and multiplied by the learning rate,
[02:35] and multiplied by the learning rate, which we set to 0.01.
[02:39] which we set to 0.01. Then we did the math,
[02:41] Then we did the math, calculated the new intercept and new
[02:44] calculated the new intercept and new slope by plugging in the old intercept
[02:46] slope by plugging in the old intercept and old slope
[02:48] and old slope and the step sizes,
[02:51] and the step sizes, and we did the math,
[02:54] and we did the math, and we ended up with a new intercept and
[02:56] and we ended up with a new intercept and a new slope.
[02:58] a new slope. Then we went back to the derivatives and
[03:00] Then we went back to the derivatives and repeated the process a lot of times
[03:03] repeated the process a lot of times until we took the maximum number of
[03:04] until we took the maximum number of steps or the steps became very, very
[03:07] steps or the steps became very, very small.
[03:09] small. In this super simple example, we were
[03:12] In this super simple example, we were just fitting a line with two parameters,
[03:14] just fitting a line with two parameters, the intercept and the slope.
[03:17] the intercept and the slope. And we only had three data points.
[03:21] And we only had three data points. So we only had three terms to compute
[03:23] So we only had three terms to compute each step for the intercept.
[03:26] each step for the intercept. And we only had three terms to compute
[03:28] And we only had three terms to compute each step for the slope.
[03:30] each step for the slope. So each step didn't require much math.
[03:34] So each step didn't require much math. But what if we had a more complicated
[03:36] But what if we had a more complicated model, like a logistic regression that
[03:39] model, like a logistic regression that used 23,000 genes to predict if someone
[03:42] used 23,000 genes to predict if someone will have a disease?
[03:44] will have a disease? Then we will have 23,000 derivatives to
[03:47] Then we will have 23,000 derivatives to plug the data into.
[03:50] plug the data into. And what if we had data from 1 million
[03:52] And what if we had data from 1 million samples?
[03:54] samples? Then we would have to calculate 1
[03:56] Then we would have to calculate 1 million terms for each of the 23,000
[03:59] million terms for each of the 23,000 derivatives.
[04:01] derivatives. In other words, we'd have to calculate
[04:03] In other words, we'd have to calculate 23 billion terms for each step.
[04:07] 23 billion terms for each step. And since it's common to take at least
[04:09] And since it's common to take at least 1,000 steps, we would calculate at least
[04:12] 1,000 steps, we would calculate at least 2.3 trillion terms.
[04:15] 2.3 trillion terms. So for big data, gradient descent is
[04:18] So for big data, gradient descent is slow.
[04:19] slow. This is where stochastic gradient
[04:21] This is where stochastic gradient descent comes in handy.
[04:24] descent comes in handy. Going back to our super simple example,
[04:27] Going back to our super simple example, stochastic gradient descent would
[04:29] stochastic gradient descent would randomly pick one sample for each step.
[04:33] randomly pick one sample for each step. And just use that one sample to
[04:35] And just use that one sample to calculate the derivatives.
[04:38] calculate the derivatives. Thus, in this super simple example,
[04:41] Thus, in this super simple example, stochastic gradient descent reduced the
[04:43] stochastic gradient descent reduced the number of terms computed by a factor of
[04:46] number of terms computed by a factor of three.
[04:47] three. If we had 1 million samples, then
[04:50] If we had 1 million samples, then stochastic gradient descent would reduce
[04:52] stochastic gradient descent would reduce the amount of terms computed by a factor
[04:54] the amount of terms computed by a factor of 1 million.
[04:56] of 1 million. So that's pretty cool.
[04:59] So that's pretty cool. Stochastic gradient descent is
[05:01] Stochastic gradient descent is especially useful when there are
[05:03] especially useful when there are redundancies in the data.
[05:06] redundancies in the data. For example, we have 12 data points, but
[05:09] For example, we have 12 data points, but there is a lot of redundancy that forms
[05:11] there is a lot of redundancy that forms three clusters.
[05:14] three clusters. So we start with a line with the
[05:16] So we start with a line with the intercept equals zero and the slope
[05:18] intercept equals zero and the slope equals one.
[05:20] equals one. Then we randomly pick this point.
[05:23] Then we randomly pick this point. So we plug in the weight, three,
[05:26] So we plug in the weight, three, and height, 3.3.
[05:29] and height, 3.3. Do the math,
[05:31] Do the math, plug in the slopes,
[05:34] plug in the slopes, then multiply by the learning rate.
[05:37] then multiply by the learning rate. Note, just like with regular gradient
[05:40] Note, just like with regular gradient descent, stochastic gradient descent is
[05:42] descent, stochastic gradient descent is sensitive to the value you choose for
[05:45] sensitive to the value you choose for the learning rate.
[05:46] the learning rate. And just like for regular gradient
[05:48] And just like for regular gradient descent, the general strategy is to
[05:51] descent, the general strategy is to start with a relatively large learning
[05:53] start with a relatively large learning rate and make it smaller with each step.
[05:57] rate and make it smaller with each step. And lastly, just like for regular
[05:59] And lastly, just like for regular gradient descent, many implementations
[06:02] gradient descent, many implementations of stochastic gradient descent will take
[06:04] of stochastic gradient descent will take care of this for you by default.
[06:07] care of this for you by default. Oh, no. It's a terminology alert.
[06:11] Oh, no. It's a terminology alert. The way the learning rate changes from
[06:13] The way the learning rate changes from relatively large to relatively small is
[06:16] relatively large to relatively small is called the schedule.
[06:18] called the schedule. So, if you fail to converge on parameter
[06:20] So, if you fail to converge on parameter estimates, try futzing with this
[06:22] estimates, try futzing with this setting.
[06:24] setting. In this simple example, however, we're
[06:27] In this simple example, however, we're just setting the learning rate to 0.01.
[06:31] just setting the learning rate to 0.01. Now, we do the math.
[06:34] Now, we do the math. Calculate the new intercept
[06:37] Calculate the new intercept and the new slope.
[06:40] and the new slope. Bam!
[06:42] Bam! The new parameters give us this new
[06:44] The new parameters give us this new line.
[06:46] line. Then, we randomly pick another point and
[06:49] Then, we randomly pick another point and calculate the intercept and slope for
[06:51] calculate the intercept and slope for another line.
[06:53] another line. Then, we just repeat everything a bunch
[06:55] Then, we just repeat everything a bunch of times.
[06:57] of times. And ultimately, we end up with a line
[06:59] And ultimately, we end up with a line where the intercept equals 0.85
[07:02] where the intercept equals 0.85 and the slope equals 0.68.
[07:06] and the slope equals 0.68. And the least squares estimates, aka the
[07:09] And the least squares estimates, aka the gold standard, gives a line where the
[07:12] gold standard, gives a line where the intercept equals 0.87
[07:14] intercept equals 0.87 and the slope equals 0.68.
[07:18] and the slope equals 0.68. Bam!
[07:21] Bam! Note, the strict definition of
[07:23] Note, the strict definition of stochastic gradient descent is to only
[07:26] stochastic gradient descent is to only use one sample per step.
[07:29] use one sample per step. However, it is much more common to
[07:31] However, it is much more common to select a small subset of data or mini
[07:34] select a small subset of data or mini batch for each step.
[07:37] batch for each step. For example, we could use three samples
[07:40] For example, we could use three samples per step instead of just one.
[07:43] per step instead of just one. Using a mini batch for each step takes
[07:46] Using a mini batch for each step takes the best of both worlds between using
[07:48] the best of both worlds between using just one sample and all of the data at
[07:50] just one sample and all of the data at each step.
[07:52] each step. Similar to using all of the data, using
[07:55] Similar to using all of the data, using a mini batch can result in more stable
[07:57] a mini batch can result in more stable estimates for the parameters in fewer
[07:59] estimates for the parameters in fewer steps.
[08:01] steps. And like using just one sample per step,
[08:04] And like using just one sample per step, using a mini batch is much faster than
[08:07] using a mini batch is much faster than using all of the data.
[08:09] using all of the data. In this example, using three samples per
[08:12] In this example, using three samples per step, we ended up with an intercept
[08:14] step, we ended up with an intercept equals 0.86
[08:16] equals 0.86 and the slope equals 0.68.
[08:20] and the slope equals 0.68. Which means that the estimate for the
[08:21] Which means that the estimate for the intercept was just a little closer to
[08:23] intercept was just a little closer to the gold standard 0.87
[08:26] the gold standard 0.87 than when we used one sample and got
[08:28] than when we used one sample and got 0.85.
[08:31] 0.85. Double bam!
[08:34] Double bam! One cool thing about stochastic gradient
[08:36] One cool thing about stochastic gradient descent is that when we get new data,
[08:39] descent is that when we get new data, we can easily use it to take another
[08:41] we can easily use it to take another step for the parameter estimates without
[08:43] step for the parameter estimates without having to start from scratch.
[08:46] having to start from scratch. In other words, we don't have to go all
[08:49] In other words, we don't have to go all the way back to the initial guesses for
[08:50] the way back to the initial guesses for the slope and intercept and redo
[08:53] the slope and intercept and redo everything.
[08:54] everything. Instead, we pick up right where we left
[08:57] Instead, we pick up right where we left off and take one more step using the new
[08:59] off and take one more step using the new sample.
[09:01] sample. So we plug in the weight from the new
[09:03] So we plug in the weight from the new sample, 1.1,
[09:06] sample, 1.1, and the height, two.
[09:09] and the height, two. Do the math.
[09:11] Do the math. Plug in the slopes.
[09:14] Plug in the slopes. Then multiply by the learning rate,
[09:16] Then multiply by the learning rate, 0.01.
[09:19] 0.01. Do the math.
[09:21] Do the math. Calculate the new intercept, not from
[09:24] Calculate the new intercept, not from the initial guess, but from the most
[09:26] the initial guess, but from the most recent estimate.
[09:28] recent estimate. And calculate the new slope from the
[09:30] And calculate the new slope from the most recent estimate.
[09:33] most recent estimate. And the new line has intercept equals
[09:35] And the new line has intercept equals 0.878
[09:37] 0.878 and slope equals 0.7.
[09:41] and slope equals 0.7. Triple bam!
[09:44] Triple bam! We updated the parameters for the line
[09:46] We updated the parameters for the line with just the new data.
[09:49] with just the new data. In summary,
[09:51] In summary, stochastic gradient descent is just like
[09:54] stochastic gradient descent is just like regular gradient descent except it only
[09:56] regular gradient descent except it only looks at one sample per step
[09:59] looks at one sample per step or a small subset or mini batch for each
[10:02] or a small subset or mini batch for each step.
[10:04] step. Stochastic gradient descent is great
[10:06] Stochastic gradient descent is great when we have tons of data and lots of
[10:08] when we have tons of data and lots of parameters.
[10:11] parameters. In these situations, regular gradient
[10:13] In these situations, regular gradient descent may not be computationally
[10:15] descent may not be computationally feasible.
[10:17] feasible. And it's cool that we can easily update
[10:20] And it's cool that we can easily update the parameters when new data shows up.
[10:23] the parameters when new data shows up. Hooray! We've made it to the end of
[10:25] Hooray! We've made it to the end of another exciting StatQuest. If you like
[10:28] another exciting StatQuest. If you like this StatQuest and want to see more,
[10:30] this StatQuest and want to see more, please subscribe. And if you want to
[10:32] please subscribe. And if you want to support StatQuest, well, consider buying
[10:35] support StatQuest, well, consider buying one or two of my original songs or
[10:36] one or two of my original songs or getting a t-shirt. The links to do this
[10:39] getting a t-shirt. The links to do this are in the description below.
[10:41] are in the description below. All right, until next time, quest on.

---
video_id: sDv4f4s2SB8
url: https://www.youtube.com/watch?v=sDv4f4s2SB8
title: Gradient Descent, Step-by-Step
channel: StatQuest with Josh Starmer
duration: 23:54
language: en
unit: L03
status: OK
---

[00:00] Gradient Descent is decent at estimating parameters. StatQuest!
[00:11] Hello!
[00:12] I'm Josh Starmer and welcome to StatQuest.
[00:15] Today we're going to learn about Gradient Descent and we're going to go through the algorithm step by step.
[00:21] Note: this StatQuest assumes you already understand the basics of least squares and
[00:26] linear regression, so if you're not already down with that, check out the Quest.
[00:31] In statistics, machine learning, and other data science fields, we optimize a lot of stuff.
[00:39] When we fit a line with linear regression, we optimize the intercept and the slope.
[00:46] When we use logistic regression, we optimize a squiggle. And when we use t-SNE, we optimize clusters.
[00:55] These are just a few examples of the stuff we optimize, there are tons more.
[01:01] The cool thing is that Gradient Descent can optimize all these things, and much more.
[01:07] So, if we learn how to optimize this line using Gradient Descent, then we'll have
[01:13] learned the strategy that optimizes this squiggle, and these clusters, and many more
[01:18] of the optimization problems we have in statistics, machine learning, and data science.
[01:25] So let's start with a simple data set.
[01:29] On the x-axis we have weight.
[01:32] On the y-axis we have height.
[01:36] If we fit a line to the data and someone tells us that they weigh 1.5, we can use
[01:42] the line to predict that they will be 1.9 tall.
[01:48] So let's learn how Gradient Descent can fit a line to data by finding the optimal values for the intercept and the slope.
[01:56] Actually, we'll start by using Gradient Descent to find the intercept.
[02:01] Then, once we understand how Gradient Descent works, we'll use it to solve for the intercept and the slope.
[02:09] So, for now, let's just plug in the Least Squares estimate for the slope, 0.64, and
[02:17] we'll use Gradient Descent to find the optimal value for the intercept.
[02:22] The first thing we do is pick a random value for the intercept.
[02:27] This is just an initial guess that gives Gradient Descent something to improve upon.
[02:33] In this case, we'll use 0, but any number will do.
[02:38] And that gives us the equation for this line.
[02:42] In this example, we will evaluate how well this line fits the data with the sum of the squared residuals.
[02:49] Note: in machine learning lingo, the sum of the squared residuals is a type of Loss Function.
[02:56] We'll talk more about Loss Functions towards the end of the video.
[03:01] We'll start by calculating this residual.
[03:05] This data point represents a person with weight 0.5 and height 1.4. We get the predicted
[03:14] height, the point on the line, by plugging weight equals 0.5 into the equation for the line.
[03:22] And the predicted height is 0.32.
[03:27] The residual is the difference between the observed height and the predicted height,
[03:32] so we calculate the difference between 1.4 and 0.32, and that gives us 1.1 for the residual.
[03:47] Here's the square of the first residual.
[03:51] The second residual is 0.4. and the third residual is 1.3. In the end, 3.1 is the sum of the squared residuals.
[04:04] Now, just for fun, we can plot that value on a graph.
[04:10] This graph has the sum of squared residuals on the y-axis, and different values for the intercept on the x-axis.
[04:19] This point represents the sum of the squared residuals when the intercept equals zero.
[04:25] However, if the intercept equals 0.25, then we would get this point on the graph.
[04:32] And if the intercept equals 0.5, then we would get this point.
[04:40] And for increasing values for the intercept we get these points.
[04:45] Of the points that we calculated for the graph, this one has the lowest sum of squared residuals.
[04:52] But is it the best we can do?
[04:55] What if the best value for the intercept is somewhere between these values?
[05:00] A slow and painful method for finding the minimal sum of the squared residuals is
[05:05] to plug and chug a bunch more values for the intercept.
[05:11] Don't despair!
[05:12] Gradient Descent is way more efficient.
[05:15] Gradient Descent only does a few calculations far from the optimal solution, and increases
[05:22] the number of calculations closer to the optimal value.
[05:27] In other words, gradient descent identifies the optimal value by taking big steps
[05:33] when it is far away, and baby steps when it is close.
[05:38] So let's get back to using gradient ascent to find the optimal value for the intercept, starting from a random value.
[05:44] In this case, the random value was zero.
[05:48] When we calculated the sum of the squared residuals, the first residual was the difference
[05:55] between the observed height, which was 1.4, and the predicted height, which came from the equation for this line.
[06:04] So we replace predicted height with the equation for the line.
[06:09] Since the individual weighs 0.5 we replace weight with 0.5. So, for this individual,
[06:19] this is their observed height and this is their predicted height.
[06:25] Note: we can now plug in any value for the intercept and get a new predicted height.
[06:31] Now let's focus on the second data point.
[06:35] Just like before, the residual is the difference between the observed height, which
[06:40] is 1.9, and the predicted height, which comes from the equation for the line.
[06:47] Snd since this individual weighs 2.3, we replace weight with 2.3.
[06:55] Now let's focus on the last person.
[06:58] Again, the residual is the difference between the observed height, which is 3.2, and
[07:05] the predicted height, which comes from the equation for the line.
[07:11] And since this person weighs 2.9, we'll replace weight with 2.9.
[07:18] Now we can easily plug in any value for the intercept and get the sum of the squared residuals.
[07:26] Thus, we now have an equation for this curve, and we can take the derivative of this
[07:32] function and determine the slope at any value for the intercept.
[07:37] So let's take the derivative of the sum of the squared residuals with respect to the intercept.
[07:44] The derivative of the sum of the squared residuals with respect to the intercept equals
[07:50] the derivative of the first part, plus the derivative of the second part, plus the derivative of the third part.
[07:59] Let's start by taking the derivative of the first part.
[08:03] First, we'll move this part of the equation up here, so that we have room to work.
[08:09] To take the derivative of this we need to apply the chain rule.
[08:15] So we start by moving the square to the front and multiply that by the derivative of the stuff inside the parentheses.
[08:26] These parts don't contain a term for the intercept, so they go away.
[08:32] Then we simplify by multiplying two by negative one.
[08:37] And this is the derivative of the first part, so we plug it in.
[08:44] Now we need to take the derivative of the next two parts.
[08:48] I'll leave that as an exercise for the viewer.
[08:52] Bam!
[08:55] Let's move the derivative up here, so that it's not taking up half the screen.
[09:00] Now that we have the derivative, Gradient Descent will use it to find where the sum of squared residuals is lowest.
[09:08] Note: if we were using least squares to solve for the optimal value for the intercept,
[09:13] we would simply find where the slope of the curve equals zero.
[09:18] In contrast gradient descent finds the minimum value by taking steps from an initial guess until it reaches the best value.
[09:27] This makes Gradient Descent very useful when it is not possible to solve for where
[09:31] the derivative equals zero. And this is why Gradient Descent can be used in so many different situations.
[09:39] Bam!
[09:41] Remember, we started by setting the intercept to a random number.
[09:45] In this case that was zero.
[09:48] So we plug zero into the derivative and we get negative 5.7. So, when the intercept
[09:55] equals 0, the slope of the curve equals negative 5.7. Note: the closer we get to
[10:03] the optimal value for the intercept, the closer the slope of the curve gets to zero.
[10:09] This means that when the slope of the curve is close to zero, then we should take
[10:14] baby steps, because we are close to the optimal value.
[10:18] And when the slope is far from zero, then we should take big steps because we are far from the optimal value.
[10:27] However, if we take a super, huge step, then we would increase the sum of the squared residuals.
[10:35] So the size of the step should be related to the slope, since it tells us if we should take a baby step or a big step.
[10:43] But we need to make sure the big step is not too big.
[10:47] Gradient Descent determines the step size by multiplying the slope by a small number called the learning rate.
[10:55] Note: we'll talk more about learning rates later.
[11:00] When the intercept equals 0, the step size equals negative 5.7. With the step size, we can calculate a new intercept.
[11:11] The new intercept is the old intercept minus the step size.
[11:16] So we plug in the numbers, and the new intercept equals 0.57.
[11:23] Bam!
[11:25] In one big step, we moved much closer to the optimal value for the intercept.
[11:31] Going back to the original data and the original line, with the intercept equals 0,
[11:36] we can see how much the residuals shrink when the intercept equals 0.57.
[11:43] Now let's take another step closer to the optimal value for the intercept. To take
[11:49] another step, we go back to the derivative and plug in the new intercept, and that
[11:54] tells us the slope of the curve equals negative 2.3.
[12:00] Now let's calculate the step size.
[12:03] By plugging in negative 2.3 for the slope, and 0.1 for the learning rate, ultimately
[12:10] the step size is negative 0.23. And the new intercept equals 0.8.
[12:18] Now we can compare the residuals when the intercept equals 0.57 to when the intercept equals 0.8.
[12:27] Overall the sum of the squared residuals is getting smaller.
[12:33] Notice that the first step was relatively large, compared to the second step.
[12:38] Now let's calculate the derivative at the new intercept: and we get negative 0.9.
[12:44] The step size equals negative 0.09, and the new intercept equals 0.89.
[12:54] Now we increase the intercept from 0.8 to 0.89, then we take another step and the
[13:00] new intercept equals 0.92. And then we take another step, and the new intercept equals
[13:08] 0.94. And then we take another step, and the new intercept equals 0.95.
[13:16] Notice how each step gets smaller and smaller the closer we get to the bottom of the curve.
[13:23] After six steps, the gradient ascent estimate for the intercept is 0.95.
[13:30] Note: the least squares estimate for the intercept is also 0.95.
[13:37] so we know that gradient descent has done its job, but without comparing its solution
[13:41] to a gold standard, how does gradient descent know to stop taking steps?
[13:47] Gradient Descent stops when the step size is very close to zero.
[13:52] The step size will be very close to zero when the slope is very close to zero.
[13:58] In practice, the minimum step size equals 0.001 or smaller.
[14:05] So if this slope equals 0.009, then we would plug in 0.009 for the slope and 0.1 for
[14:15] the learning rate and get 0.0009, which is smaller than 0.001, so gradient descent would stop.
[14:27] That said, gradient descent also includes a limit on the number of steps it will take before giving up.
[14:34] In practice, the maximum number of steps equals 1000 or greater.
[14:39] So, even if the step size is large, if there have been more than the maximum number of steps, gradient descent will stop.
[14:49] Okay, let's review what we've learned so far.
[14:53] The first thing we did is decide to use the sum of the squared residuals as the loss
[14:57] function to evaluate how well a line fits the data.
[15:02] Then, we took the derivative of the sum of the squared residuals. In other words,
[15:07] we took the derivative of the loss function.
[15:10] Then, we picked a random value for the intercept, in this case we set the intercept to be equal to zero.
[15:17] Then, we calculated the derivative when the intercept equals zero, plugged that slope
[15:23] into the step size calculation, and then calculated the new intercept, the difference
[15:28] between the old intercept and the step size.
[15:32] Lastly, we plugged the new intercept into the derivative and repeated everything until step size was close to zero.
[15:40] Double bam!
[15:44] Now that we understand how gradient descent can calculate the intercept, let's talk
[15:49] about how to estimate the intercept and the slope.
[15:53] Just like before, we'll use the sum of the squared residuals as the loss function.
[15:59] This is a 3D graph of the loss function for the different values for the intercept and the slope.
[16:06] This axis is the sum of the squared residuals, this axis represents different values
[16:13] for the slope, and this axis represents different values for the intercept.
[16:19] We want to find the values for the intercept and slope that give us the minimum sum of the squared residuals.
[16:26] So, just like before, we need to take the derivative of this function.
[16:32] And just like before, we'll take the derivative with respect to the intercept.
[16:38] But, unlike before, we'll also take the derivative with respect to the slope.
[16:44] We'll start by taking the derivative with respect to the intercept.
[16:48] Just like before, we'll take the derivative of each part.
[16:53] And, just like before, we'll use the chain rule and move the square to the front,
[16:59] and multiply that by the derivative of the stuff inside the parentheses.
[17:07] [Music] Since we are taking the derivative with respect to the intercept, we treat
[17:12] the slope like a constant, and the derivative of a constant is zero.
[17:17] So, we end up with negative one, just like before.
[17:23] Then we simplify by multiplying two by negative one.
[17:28] And this is the derivative of the first part.
[17:32] So we plug it in.
[17:35] Likewise, we replace these terms with their derivatives.
[17:39] So this whole thing is the derivative of the sum of squared residuals with respect to the intercept.
[17:46] Now let's take the derivative of the sum of the squared residuals with respect to the slope.
[17:52] Just like before, we take the derivative of each part and, just like before, we'll
[17:59] use the chain rule to move the square to the front and multiply that by the derivative of the stuff inside the parentheses.
[18:11] Since we are taking the derivative with respect to the slope, we treat the intercept
[18:16] like a constant and the derivative of a constant is zero.
[18:21] So we end up with negative 0.5. Then we simplify by moving the negative 0.5 to the front.
[18:32] Note: I left the 0.5 in bold instead of multiplying it by 2 to remind us that 0.5 is the weight for the first sample.
[18:43] And this is the derivative of the first part.
[18:48] So we plug it in.
[18:50] Likewise, we replace these terms with their derivatives.
[18:56] Again, 2.3 and 2.9 are in bold to remind us that they are the weights of the second and third samples.
[19:05] Here's the derivative of the sum of the squared residuals with respect to the intercept,
[19:10] and here's the derivative with respect to the slope.
[19:14] Note: when you have two or more derivatives of the same function they are called a gradient.
[19:21] We will use this gradient to descend to the lowest point in the loss function, which,
[19:26] in this case, is the sum of the squared residuals.
[19:30] Thus, this is why the algorithm is called Gradient Descent.
[19:35] Bam!
[19:37] Just like before, we'll start by picking a random number for the intercept. In this
[19:42] case, we'll set the intercept to be equal to zero, and we'll pick a random number for the slope.
[19:48] In this case we'll set the slope to be 1.
[19:52] Thus, this line, with intercept equals 0 and slope equals 1, is where we will start.
[20:00] Now, let's plug in 0 for the intercept and 1 for the slope.
[20:05] And that gives us two slopes.
[20:08] Now, we plug the slopes into the step size formulas, and multiply by the learning rate, which this time we set to 0.01.
[20:19] Note: The larger learning rate that we used in the first example doesn't work this time.
[20:25] Even after a bunch of steps, Gradient Descent doesn't arrive at the correct answer.
[20:30] This means that Gradient Descent can be very sensitive to the learning rate.
[20:35] The good news is that, in practice, a reasonable learning rate can be determined automatically
[20:41] by starting large and getting smaller with each step.
[20:45] So, in theory, you shouldn't have to worry too much about the learning rate.
[20:51] Anyway, we do the math and get two step sizes.
[20:55] Now we calculate the new intercept and new slope by plugging in the old intercept and the old slope, and the step sizes.
[21:05] And we end up with a new intercept and a new slope.
[21:10] This is the line we started with and this is the new line after the first step.
[21:17] Now we just repeat what we did until all of the step sizes are very small, or we reach the maximum number of steps.
[21:26] This is the best fitting line, with intercept equals 0.95 and slope equals 0.64, the same values we get from least squares.
[21:37] Double bam!
[21:40] We now know how Gradient Descent optimizes two parameters, the slope and the intercept.
[21:46] If we had more parameters then we just take more derivatives and everything else stays the same.
[21:53] Triple bam!
[21:55] Note: the sum of the squared residuals is just one type of Loss Function.
[22:01] However, there are tons of other loss functions that work with other types of data.
[22:07] Regardless of which Loss Function you use, Gradient Descent works the same way.
[22:13] Step 1: take the derivative of the loss function for each parameter in it.
[22:19] In fancy machine learning lingo, take the gradient of the loss function.
[22:24] Step 2: pick random values for the parameters.
[22:29] Step 3: plug the parameter values into the derivatives (ahem, the gradient).
[22:36] Step 4: calculate the step sizes.
[22:40] Step 5: calculate the new parameters.
[22:44] Now go back to step 3 and repeat&nbsp;until step size is very small or you reach the maximum number of steps.
[22:52] One last thing before we're done. In our example we only had three data points, so the math didn't take very long.
[23:02] But when you have millions of data points it can take a long time.
[23:06] So there is a thing called Stochastic Gradient Descent that uses a randomly selected
[23:12] subset of the data at every step rather than the full data set.
[23:16] This reduces the time spent calculating the derivatives of the loss function.
[23:22] That's all.
[23:24] Stochastic Gradient Descent sounds fancy, but it's no big deal.
[23:29] Hooray!
[23:30] We've made it to the end of another exciting StatQuest.
[23:33] If you like this StatQuest and want to see more, please subscribe.
[23:37] And if you want to support StatQuest, well, consider buying one or two of my original
[23:42] songs, or buying a StatQuest t-shirt or hoodie.
[23:45] The links&nbsp;are in the description below.
[23:48] Alright, until next time.
[23:50] Quest on!

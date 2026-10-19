---
video_id: PaFPbb66DxQ
url: https://www.youtube.com/watch?v=PaFPbb66DxQ
title: The Main Ideas of Fitting a Line to Data (The Main Ideas of Least Squares and Linear Regression.)
channel: StatQuest with Josh Starmer
duration: 9:21
language: en
unit: L03
status: OK
---

[00:02] When we go on a quest and that quest is really awesome. It's that StatQuest
[00:10] Yeah, yeah, yeah
[00:13] Hello, and welcome to StatQuest. StatQuest is brought to you by the friendly folks in the genetics Department at the University of North
[00:21] Carolina at Chapel Hill.
[00:23] Today, we're going to talk about fitting a line to Data. aka
[00:28] Least Squares aka
[00:30] Linear regression. Now let's get to it.
[00:34] Okay, you worked really hard. You did the experiment and now you got some data. Here it is plotted on an XY graph.
[00:43] We usually like to add a line to our data so we can see what the trend is.
[00:48] But is this the best line we should use?
[00:52] Or does this new line fit the data even better?
[00:56] Or what about this line is it better or worse than the other options?
[01:02] A horizontal line that cuts through the average y value of our data is probably the worst fit of all.
[01:09] However, it gives us a good starting point for talking about how to find the optimal line to fit our data.
[01:17] So now let's focus on this horizontal line.
[01:21] It cuts through the average Y value which is 3.5.
[01:27] Let's just call this point B. Because different data sets will have different average values on the Y axis.
[01:35] That is to say the Y value for this line is B, and
[01:41] for this particular data set B equals 3.5.
[01:46] We can measure how well this line fits the data by seeing how close it is to the data points.
[01:53] We'll start with the point in the lower left-hand corner of the graph with Coordinates X-One Y-one.
[02:01] We can now draw a line from this point up to the line that cuts across the average Y value for this data set.
[02:10] The distance between the line and the first data point
[02:13] equals B minus
[02:15] Y1.
[02:17] The distance between the line and the second data point is B minus Y2?
[02:24] So far the total distance between the data points and the line is the sum of the two distances and we
[02:33] can calculate the distance between the line and the third point that equals B minus Y3.
[02:41] Now we've added the third distance to our total sum.
[02:45] The distance for the fourth point is B minus Y4.
[02:50] Note Y4 is greater than B. Because it's above the horizontal line, so this value will be negative.
[02:59] That's no good, since it will subtract from the total and make the overall fit appear better than it really is.
[03:08] The fifth data point is even higher relative to the horizontal line this distance is going to be very negative.
[03:17] Back in the day when they were first working this out
[03:20] they probably tried taking the absolute value of everything and then discovered that it made the math pretty tricky.
[03:28] So they ended up squaring each term.
[03:31] Squaring ensures that each term is positive.
[03:36] Here's the equation that shows the total distance the data points have from the horizontal line.
[03:42] In this specific example,
[03:45] 24.62 is our measure of how well this line fits the data.
[03:51] It's called the sum of squared residuals
[03:54] because the residuals are the differences between the real data and the line and
[04:00] we are summing the square of these values. Now
[04:04] let's see how good the fit is if we rotate the line a little bit. In
[04:09] this case, the sum of squared residuals
[04:13] equals 18.72.
[04:16] This is better than before.
[04:19] Does this fit improve if we rotate a little more?
[04:24] Yes,
[04:25] the sum of squared residuals
[04:27] now equals 14.05. That value keeps going down the more we rotate the line.
[04:35] What if we rotate the line a whole lot?
[04:39] Well as you can see the fit gets worse, in this case the sum of squared residuals is
[04:46] 31.71. so there's a sweet spot in between
[04:50] horizontal and two vertical.
[04:53] To find that sweet spot
[04:54] let's start with the generic line equation.
[04:57] This is Y equals AX or A times X plus B. A
[05:04] is the slope of the line and B
[05:07] is the
[05:09] Y-intercept of the line. That's the location on the Y axis that the line crosses when X equals 0.
[05:18] We want to find the optimal values for A and B so that we minimize the sum of squared residuals.
[05:26] In more general math terms the sum of squared residuals is this complicated mathematical equation.
[05:34] But it's actually not that complicated,
[05:36] this first part is the value of the line at X1 and
[05:42] this second part is the observed value at X1.
[05:46] So really all we're doing in this part of the equation is calculating the distance between the line and the observed value.
[05:54] So this is no big deal.
[05:56] Since we want the line that will give us the smallest sum of squares
[06:01] this method for finding the best values for A and B is called least squares.
[06:08] If we plotted the sum of squared residuals
[06:11] versus each rotation we get something like this, where on the Y axis we have the sum of squared residuals
[06:18] and on the X axis we've got each different rotation of the line.
[06:23] We see that the sum of squared residuals goes down when we start rotating the line, but that it's possible to rotate the line
[06:31] too far in the sum of squared residual starts going back up again.
[06:36] How do we find the optimal rotation for the line?
[06:40] Well, we take the derivative of this function.
[06:44] The derivative tells us the slope of the function at every point.
[06:48] The slope at the point on the far left side is pretty steep. As
[06:54] we move to the right we see that the slope isn't as steep.
[06:59] The slope at the best point where we have the least squares is zero
[07:05] after that the slope starts getting steep again.
[07:09] Let's go back to that middle point where we have the least squares value and the slope is zero.
[07:17] Remember the different rotations are just different values for A the slope and B the intercept.
[07:25] We can use a 3D graph to show how different values for the slope and intercept result in different sums of squares.
[07:34] In this graph
[07:35] the intercept is the Z axis so it's going back sort of deep into your computer screen
[07:41] and if we select one value for the intercept.
[07:45] For example, assume we set the intercept value to be 3.
[07:50] Then we could change values for the slope and see how an intercept of 3
[07:57] plus different values for the slope would affect the sum of squared residuals.
[08:04] Anyways, we do that for bunches of different intercepts and slopes.
[08:09] Taking the derivatives of both the slope and the intercepts tells us where the optimal values are for the best fit.
[08:17] Note: no one ever solves this problem by hand, this is done on a computer. So for most people
[08:24] It's not essential to know how to take these derivatives.
[08:28] However, it's essential to understand the concepts.
[08:33] Big important concept number one,
[08:35] we want to minimize the square of the distance between the observed values and the line.
[08:43] Big important concept number two,
[08:46] we do this by taking the derivative and finding where it is equal to zero.
[08:52] The final line
[08:54] minimizes the sums of squares. It gives the least squares between it and the real data.
[09:01] In this case, the line is defined by the following equation
[09:05] Y = 0.77 * X + 0.66.
[09:12] Hooray, we've made it to the end of another StatQuest.
[09:16] Tune in next time for another exciting adventure in statistics land.

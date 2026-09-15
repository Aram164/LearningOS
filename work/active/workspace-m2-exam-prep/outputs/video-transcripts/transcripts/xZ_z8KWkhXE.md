---
video_id: xZ_z8KWkhXE
url: https://www.youtube.com/watch?v=xZ_z8KWkhXE
title: Pearson's Correlation, Clearly Explained!!!
channel: StatQuest with Josh Starmer
duration: 19:13
language: en
unit: L03
status: OK
---

[00:00] correlation it's the sensation across
[00:06] correlation it's the sensation across the nation stack quests hello I'm Josh
[00:13] the nation stack quests hello I'm Josh starburns welcome to stack quest today
[00:16] starburns welcome to stack quest today is part two in our series on covariance
[00:18] is part two in our series on covariance and correlation this time we're going to
[00:21] and correlation this time we're going to talk about correlation however before we
[00:25] talk about correlation however before we dive deep into correlation I want to
[00:27] dive deep into correlation I want to talk about relationships not the fun
[00:30] talk about relationships not the fun and/or confusing kind we sometimes find
[00:33] and/or confusing kind we sometimes find ourselves in will you hold my hand um
[00:38] ourselves in will you hold my hand um you don't have a hand
[00:41] you don't have a hand you're just a stick figure dang instead
[00:47] you're just a stick figure dang instead I want to talk about the relationships
[00:49] I want to talk about the relationships between data on the x-axis and data on
[00:53] between data on the x-axis and data on the y-axis
[00:55] the y-axis in this example we're looking at mRNA
[00:58] in this example we're looking at mRNA transcripts from gene X in five
[01:00] transcripts from gene X in five different cells on the x-axis and from
[01:04] different cells on the x-axis and from gene Y in the same five different cells
[01:07] gene Y in the same five different cells on the y-axis
[01:10] on the y-axis however if mRNA transcripts doesn't mean
[01:13] however if mRNA transcripts doesn't mean anything to you
[01:14] anything to you imagine we went into five different
[01:16] imagine we went into five different grocery stores and put the number of
[01:18] grocery stores and put the number of green apples on the x-axis in the number
[01:22] green apples on the x-axis in the number of red apples on the y-axis
[01:25] of red apples on the y-axis each pair of measurements were taken
[01:28] each pair of measurements were taken from a single cell or grocery store and
[01:30] from a single cell or grocery store and can be represented by a blue dot
[01:34] can be represented by a blue dot we can see that in general relatively
[01:38] we can see that in general relatively low values for gene X are paired with
[01:40] low values for gene X are paired with relatively low values for gene Y and
[01:43] relatively low values for gene Y and relatively high values for gene X are
[01:46] relatively high values for gene X are paired with relatively high values for
[01:48] paired with relatively high values for gene y
[01:50] gene y we can use a straight line with a
[01:53] we can use a straight line with a positive slope to represent this trend
[01:55] positive slope to represent this trend and if someone told us that they
[01:58] and if someone told us that they collected a new measurement for gene X
[02:00] collected a new measurement for gene X 20 then we can use the line to predict
[02:05] 20 then we can use the line to predict that when gene X equals 20 then the
[02:08] that when gene X equals 20 then the value for gene Y should be somewhere
[02:11] value for gene Y should be somewhere around 27
[02:14] alternatively if someone gave us a value
[02:17] alternatively if someone gave us a value for gene Y we could use the trend to
[02:21] for gene Y we could use the trend to predict a range of values for gene X
[02:26] both cases we made guesses based on the trend we observed in the data
[02:32] trend we observed in the data if the data were closer to the trendline
[02:35] if the data were closer to the trendline then given a gene X value
[02:38] then given a gene X value we might guess that the value for gene Y
[02:40] we might guess that the value for gene Y falls in a smaller range
[02:44] falls in a smaller range in this case the closer the data are to
[02:47] in this case the closer the data are to the line the more gene X can tell us
[02:49] the line the more gene X can tell us about gene y alternatively we could say
[02:54] about gene y alternatively we could say that the relationship between gene X and
[02:56] that the relationship between gene X and gene Y is relatively strong
[03:01] the data were further from the trendline then we might guess that the value for
[03:05] then we might guess that the value for Jean Y falls in a larger range
[03:09] Jean Y falls in a larger range in this case we could say that the
[03:12] in this case we could say that the values for gene X tell us less about the
[03:14] values for gene X tell us less about the values for gene y alternatively we could
[03:19] values for gene y alternatively we could say that the relationship between gene X
[03:21] say that the relationship between gene X and gene Y is relatively weak
[03:25] and gene Y is relatively weak note just to be clear all we are saying
[03:28] note just to be clear all we are saying is that we observed that low values for
[03:31] is that we observed that low values for gene X tend to be paired with low values
[03:34] gene X tend to be paired with low values for gene Y and that high values for gene
[03:38] for gene Y and that high values for gene X tend to be paired with relatively high
[03:41] X tend to be paired with relatively high values for gene Y and that this
[03:44] values for gene Y and that this observation suggests a trend that we can
[03:48] observation suggests a trend that we can use to make predictions and inferences
[03:50] use to make predictions and inferences aka
[03:51] aka educated guesses we are not saying that
[03:55] educated guesses we are not saying that a low value for gene X causes gene Y to
[03:59] a low value for gene X causes gene Y to have a low value or that a high value
[04:03] have a low value or that a high value for gene Y causes gene X to have a high
[04:07] for gene Y causes gene X to have a high value in other words we are not ruling
[04:10] value in other words we are not ruling out the possibility that something else
[04:13] out the possibility that something else causes the trend that we observe small
[04:16] causes the trend that we observe small bam so far we have looked at a
[04:20] bam so far we have looked at a relatively weak relationship and a
[04:23] relatively weak relationship and a relatively strong relationship we can
[04:26] relatively strong relationship we can quantify the strength of a relationship
[04:29] quantify the strength of a relationship with correlation
[04:31] with correlation in other words these data with a
[04:34] in other words these data with a relatively weak relationship have a
[04:36] relatively weak relationship have a small correlation value these data with
[04:41] small correlation value these data with a moderate relationship have a moderate
[04:43] a moderate relationship have a moderate correlation value
[04:45] correlation value and these data with a strong
[04:48] and these data with a strong relationship have a relatively large
[04:50] relationship have a relatively large correlation value the maximum value for
[04:54] correlation value the maximum value for correlation is 1
[04:57] correlation is 1 correlation equals one when a straight
[05:00] correlation equals one when a straight line with a positive slope can go
[05:02] line with a positive slope can go through the center of every data point
[05:05] through the center of every data point this means that if someone gave us a
[05:07] this means that if someone gave us a value for gene X
[05:10] value for gene X then we could guess that jean y had a
[05:12] then we could guess that jean y had a value in a very very narrow range
[05:16] value in a very very narrow range note correlation does not depend on the
[05:20] note correlation does not depend on the scale of the data
[05:22] scale of the data in fact I intentionally omitted putting
[05:25] in fact I intentionally omitted putting numbers on the axes because they do not
[05:27] numbers on the axes because they do not affect correlation at all
[05:30] affect correlation at all in other words regardless of the scale
[05:33] in other words regardless of the scale of the data correlation equals one when
[05:36] of the data correlation equals one when a straight line with a positive slope
[05:37] a straight line with a positive slope can go through all of the data
[05:41] can go through all of the data that means that correlation can equal
[05:43] that means that correlation can equal one when the slope is large and when the
[05:47] one when the slope is large and when the slope is small
[05:49] slope is small note when a straight line with a
[05:52] note when a straight line with a positive slope goes through the data
[05:54] positive slope goes through the data correlation equals one regardless of how
[05:57] correlation equals one regardless of how much data we have
[05:59] much data we have for example if we only had two data
[06:02] for example if we only had two data points then we can draw a straight line
[06:04] points then we can draw a straight line with a positive slope by just connecting
[06:07] with a positive slope by just connecting the two dots
[06:09] the two dots and then correlation equals one and that
[06:12] and then correlation equals one and that makes the relationship appear strong
[06:16] makes the relationship appear strong but we should not have any confidence in
[06:18] but we should not have any confidence in predictions made with this line because
[06:21] predictions made with this line because we have so little data
[06:24] we have so little data to understand why we should have low
[06:26] to understand why we should have low confidence in correlations made with
[06:28] confidence in correlations made with small datasets let's start with an empty
[06:32] small datasets let's start with an empty graph and draw two random points on it
[06:37] graph and draw two random points on it then just like before we could draw a
[06:40] then just like before we could draw a straight line that goes through the
[06:42] straight line that goes through the center of each point just by connecting
[06:44] center of each point just by connecting the dots and that means correlation
[06:48] the dots and that means correlation equals one for these two randomly drawn
[06:50] equals one for these two randomly drawn dots
[06:52] dots in fact we can always draw a straight
[06:55] in fact we can always draw a straight line between any two random dots
[06:59] now let's go back to the original data
[07:02] now let's go back to the original data and imagine that instead of two pairs of
[07:04] and imagine that instead of two pairs of measurements we had three pairs of
[07:07] measurements we had three pairs of measurements
[07:09] measurements now just like before since we can draw a
[07:12] now just like before since we can draw a straight line through all three points
[07:14] straight line through all three points correlation equals one however now we
[07:18] correlation equals one however now we can have more confidence in the
[07:20] can have more confidence in the predictions we make with this line
[07:23] predictions we make with this line this is because if we started with an
[07:25] this is because if we started with an empty graph and drew three random points
[07:29] empty graph and drew three random points on it then even though it's easy to draw
[07:32] on it then even though it's easy to draw a straight line to connect any two
[07:34] a straight line to connect any two points there is a very small chance that
[07:37] points there is a very small chance that we will be able to draw a straight line
[07:39] we will be able to draw a straight line through all three points ultimately the
[07:44] through all three points ultimately the probability that we can connect three
[07:46] probability that we can connect three randomly drawn points with a straight
[07:48] randomly drawn points with a straight line is very small and thus we can have
[07:52] line is very small and thus we can have more confidence that the observed
[07:54] more confidence that the observed correlation isn't just the result of
[07:56] correlation isn't just the result of random chance
[07:58] random chance in general the more data we have the
[08:02] in general the more data we have the more confidence we have in the
[08:04] more confidence we have in the predictions we make with the line
[08:07] predictions we make with the line because the probability that we can draw
[08:10] because the probability that we can draw a straight line through the same number
[08:12] a straight line through the same number of randomly placed points gets smaller
[08:14] of randomly placed points gets smaller and smaller with each additional point
[08:18] and smaller with each additional point note we could draw a squiggly line that
[08:21] note we could draw a squiggly line that connects all of the dots
[08:24] connects all of the dots but when we're talking about correlation
[08:26] but when we're talking about correlation were only talking about using straight
[08:28] were only talking about using straight lines
[08:31] lines oh no it's the dreaded terminology alert
[08:34] oh no it's the dreaded terminology alert for correlation a p-value tells us the
[08:37] for correlation a p-value tells us the probability that randomly drawn dots
[08:39] probability that randomly drawn dots will result in a similarly strong
[08:41] will result in a similarly strong relationship or stronger
[08:45] relationship or stronger thus the smaller the p-value the more
[08:48] thus the smaller the p-value the more confidence we have in the predictions we
[08:50] confidence we have in the predictions we make with the line in this case the
[08:53] make with the line in this case the p-value is crazy small 2.2 times 10 to
[08:57] p-value is crazy small 2.2 times 10 to the negative 16 which means that the
[09:01] the negative 16 which means that the probability of random data creating a
[09:03] probability of random data creating a similarly strong or stronger
[09:05] similarly strong or stronger relationship is crazy small
[09:09] to summarize what we've talked about so far the maximum value for correlation
[09:14] far the maximum value for correlation one occurs whenever you can draw a
[09:17] one occurs whenever you can draw a straight line with a positive slope that
[09:20] straight line with a positive slope that goes through all of the data and our
[09:23] goes through all of the data and our confidence in how useful the
[09:25] confidence in how useful the relationship is depends on how much data
[09:27] relationship is depends on how much data we have
[09:29] we have of these three examples we should have
[09:32] of these three examples we should have the least confidence in this
[09:33] the least confidence in this relationship since it is supported by
[09:36] relationship since it is supported by the least amount of data and we should
[09:39] the least amount of data and we should have the most confidence in this
[09:41] have the most confidence in this relationship since it is supported by
[09:43] relationship since it is supported by the most data and has the smallest
[09:45] the most data and has the smallest p-value BAM
[09:50] when a straight line with a negative slope can go through the center of every
[09:54] slope can go through the center of every data point then the correlation equals
[09:57] data point then the correlation equals negative one
[09:59] negative one since a straight line can go through all
[10:01] since a straight line can go through all of the data points correlation equals
[10:04] of the data points correlation equals negative one implies that there is a
[10:06] negative one implies that there is a strong relationship in the data and if
[10:09] strong relationship in the data and if someone gives us a value for gene X then
[10:12] someone gives us a value for gene X then we can guess a value for gene Y within a
[10:15] we can guess a value for gene Y within a very narrow range
[10:17] very narrow range just like before our confidence in that
[10:20] just like before our confidence in that guess which we quantify with a p-value
[10:23] guess which we quantify with a p-value depends on how much data we have if we
[10:27] depends on how much data we have if we had a lot of data we could have a lot of
[10:29] had a lot of data we could have a lot of confidence in the guess because the
[10:31] confidence in the guess because the p-value would be super small and the
[10:35] p-value would be super small and the less data we have the less confidence we
[10:38] less data we have the less confidence we have in the guess because the p-value
[10:39] have in the guess because the p-value gets larger
[10:43] gets larger like before as long as a straight line
[10:45] like before as long as a straight line goes through all of the data and the
[10:47] goes through all of the data and the slope of the line is negative
[10:49] slope of the line is negative correlation equals negative one when the
[10:51] correlation equals negative one when the slope is large and when the slope is
[10:54] slope is large and when the slope is small BAM so far we've seen that when
[11:00] small BAM so far we've seen that when the slope of the line is negative the
[11:02] the slope of the line is negative the strongest relationship has correlation
[11:05] strongest relationship has correlation equal to negative one and when the slope
[11:08] equal to negative one and when the slope of the line is positive the strongest
[11:10] of the line is positive the strongest relationship has correlation equal to
[11:13] relationship has correlation equal to one
[11:15] one in both cases if a straight line cannot
[11:18] in both cases if a straight line cannot go through all of the data then we will
[11:20] go through all of the data then we will get correlation values closer to zero
[11:22] get correlation values closer to zero and the worse the fit the closer the
[11:26] and the worse the fit the closer the correlation gets to zero
[11:29] correlation gets to zero and when there is no relationship that
[11:32] and when there is no relationship that we can represent with a straight line
[11:34] we can represent with a straight line correlation equals zero when correlation
[11:38] correlation equals zero when correlation equals zero a value on the x-axis
[11:42] equals zero a value on the x-axis doesn't tell us anything about what to
[11:44] doesn't tell us anything about what to expect on the y-axis because there is no
[11:48] expect on the y-axis because there is no reason to choose one value over another
[11:51] reason to choose one value over another BAM as long as the correlation value is
[11:56] BAM as long as the correlation value is not zero we can still use the line to
[12:01] not zero we can still use the line to make inferences
[12:03] make inferences but our guesses become more refined the
[12:05] but our guesses become more refined the closer the correlation values get to
[12:07] closer the correlation values get to negative one or one
[12:11] negative one or one and just like before our confidence in
[12:14] and just like before our confidence in our inferences depends on the amount of
[12:16] our inferences depends on the amount of data we have collected and the p-value
[12:19] data we have collected and the p-value in the left graph we have very little
[12:22] in the left graph we have very little confidence in the trim because we have
[12:24] confidence in the trim because we have very little data and the p value equals
[12:27] very little data and the p value equals 0.8
[12:29] 0.8 in the middle we have moderate
[12:32] in the middle we have moderate confidence in the trend because we have
[12:34] confidence in the trend because we have more data and the p value equals 0.08 on
[12:38] more data and the p value equals 0.08 on the right we have a lot of confidence in
[12:41] the right we have a lot of confidence in the trend because we have even more data
[12:43] the trend because we have even more data in the p value equals zero point zero
[12:46] in the p value equals zero point zero zero eight note the correlation equals
[12:51] zero eight note the correlation equals zero point three in all three examples
[12:53] zero point three in all three examples in this case increasing the sample size
[12:57] in this case increasing the sample size did not increase correlation and that
[13:01] did not increase correlation and that means adding data did not refine our
[13:04] means adding data did not refine our guests
[13:06] guests all it did was increase our confidence
[13:08] all it did was increase our confidence in the guess
[13:11] in the guess thus our guesses will probably be pretty
[13:13] thus our guesses will probably be pretty bad in all three cases however we'll
[13:17] bad in all three cases however we'll have the most confidence in the bad
[13:19] have the most confidence in the bad guest that came from this data
[13:22] guest that came from this data in other words just because you have a
[13:25] in other words just because you have a lot of data and you have a lot of
[13:27] lot of data and you have a lot of confidence in your guests
[13:29] confidence in your guests if the correlation value is small your
[13:32] if the correlation value is small your guests will still be bad double bam if
[13:37] guests will still be bad double bam if you know how to calculate variance and
[13:40] you know how to calculate variance and covariance calculating correlation is a
[13:43] covariance calculating correlation is a snap note if you're not already familiar
[13:47] snap note if you're not already familiar with the concepts of variance and
[13:49] with the concepts of variance and covariance check out the quests the
[13:51] covariance check out the quests the links are in the description below
[13:54] links are in the description below if this were the data then the
[13:58] if this were the data then the correlation equals the covariance of
[14:01] correlation equals the covariance of gene X and gene Y divided by the square
[14:05] gene X and gene Y divided by the square root of the variance for gene X times
[14:09] root of the variance for gene X times the square root of the variance for gene
[14:11] the square root of the variance for gene y
[14:13] y as we saw in the stat quest on
[14:16] as we saw in the stat quest on covariance the numerator can be any
[14:18] covariance the numerator can be any value between positive and negative
[14:21] value between positive and negative infinity depending on whether the slope
[14:24] infinity depending on whether the slope of the line that represents the
[14:26] of the line that represents the relationship is positive or negative how
[14:30] relationship is positive or negative how far the data are spread out around the
[14:33] far the data are spread out around the means and the scale of the data
[14:38] means and the scale of the data thus when we calculate correlation the
[14:41] thus when we calculate correlation the denominator squeezes the covariance to
[14:44] denominator squeezes the covariance to be a number from negative 1 to 1 in
[14:47] be a number from negative 1 to 1 in other words the denominator ensures that
[14:50] other words the denominator ensures that the scale of the data does not affect
[14:53] the scale of the data does not affect the correlation value and this makes
[14:55] the correlation value and this makes correlations much easier to interpret
[14:58] correlations much easier to interpret when the data all fall on a straight
[15:01] when the data all fall on a straight line with a positive or negative slope
[15:04] line with a positive or negative slope then the covariance and the product of
[15:07] then the covariance and the product of the square root of the variance terms
[15:09] the square root of the variance terms are the same and division gives us 1 or
[15:12] are the same and division gives us 1 or negative 1 depending on the slope
[15:16] negative 1 depending on the slope when the data do not fall on a straight
[15:18] when the data do not fall on a straight line with a positive or negative slope
[15:21] line with a positive or negative slope then the covariance accounts for less of
[15:24] then the covariance accounts for less of the variance in the data and the
[15:26] the variance in the data and the correlation is closer to zero
[15:29] correlation is closer to zero as we saw in the stat quest on
[15:32] as we saw in the stat quest on covariance the covariance value for this
[15:35] covariance the covariance value for this data is 116 so the denominator will
[15:40] data is 116 so the denominator will squeeze 116 down to a value from
[15:43] squeeze 116 down to a value from negative 1 to 1
[15:46] negative 1 to 1 the variants in the gene X data is 100
[15:49] the variants in the gene X data is 100 1.8 and the variants in the gene Y data
[15:53] 1.8 and the variants in the gene Y data is 160 point 3 and when we do the math
[15:58] is 160 point 3 and when we do the math we get 0.9
[16:01] we get 0.9 like I mentioned earlier we can quantify
[16:04] like I mentioned earlier we can quantify our confidence in this relationship with
[16:06] our confidence in this relationship with a p-value
[16:08] a p-value the smaller the p-value the more
[16:11] the smaller the p-value the more confidence we can have in the guesses we
[16:13] confidence we can have in the guesses we make in this case the p-value is 0.03
[16:19] make in this case the p-value is 0.03 that means that there is a 3% chance
[16:22] that means that there is a 3% chance that random data could produce a
[16:24] that random data could produce a similarly strong relationship or
[16:27] similarly strong relationship or stronger
[16:29] stronger triple bam
[16:32] before we go there's one last important
[16:35] before we go there's one last important thing I want to mention about
[16:36] thing I want to mention about correlation even though correlation
[16:40] correlation even though correlation values are way easier to interpret then
[16:42] values are way easier to interpret then covariance values they are still not
[16:45] covariance values they are still not super easy to interpret for example it's
[16:49] super easy to interpret for example it's not super obvious that this relationship
[16:51] not super obvious that this relationship where correlation equals zero point nine
[16:54] where correlation equals zero point nine is twice as good as making predictions
[16:57] is twice as good as making predictions as this relationship where correlation
[17:01] as this relationship where correlation equals zero point six four
[17:03] equals zero point six four the good news is that R squared which is
[17:07] the good news is that R squared which is related to correlation solves this
[17:09] related to correlation solves this problem the better news is that if you
[17:13] problem the better news is that if you want to learn more about r-squared you
[17:15] want to learn more about r-squared you can check out these quests the links are
[17:18] can check out these quests the links are in the description below
[17:20] in the description below pS another awesome thing about R squared
[17:24] pS another awesome thing about R squared is that it can quantify relationships
[17:26] is that it can quantify relationships that are more complicated than simple
[17:28] that are more complicated than simple straight lines
[17:31] straight lines in summary correlation quantifies the
[17:35] in summary correlation quantifies the strengths of relationships if you have a
[17:38] strengths of relationships if you have a weak relationship then you will have a
[17:41] weak relationship then you will have a small correlation value if you have a
[17:44] small correlation value if you have a moderate relationship then you'll have a
[17:46] moderate relationship then you'll have a moderate correlation value and if you
[17:49] moderate correlation value and if you have a strong relationship then you will
[17:52] have a strong relationship then you will have a large correlation value
[17:55] have a large correlation value correlation values go from negative one
[17:57] correlation values go from negative one which is the strongest linear
[17:59] which is the strongest linear relationship with a negative slope to
[18:02] relationship with a negative slope to one which is the strongest linear
[18:04] one which is the strongest linear relationship with a positive slope in
[18:07] relationship with a positive slope in both cases if a straight line cannot go
[18:11] both cases if a straight line cannot go through all of the data then we will get
[18:13] through all of the data then we will get correlation values closer to zero and
[18:16] correlation values closer to zero and the worse the fit the closer the
[18:19] the worse the fit the closer the correlation values get to zero and when
[18:23] correlation values get to zero and when there is no relationship that we can
[18:25] there is no relationship that we can represent with a straight line
[18:27] represent with a straight line correlation equals zero lastly our
[18:31] correlation equals zero lastly our confidence in the inferences depends on
[18:33] confidence in the inferences depends on the amount of data we have collected and
[18:35] the amount of data we have collected and the p-value
[18:38] the p-value the more data we have the smaller the
[18:40] the more data we have the smaller the p-value and the more confidence we have
[18:42] p-value and the more confidence we have in our inferences BAM hooray
[18:49] in our inferences BAM hooray we made it to the end of another
[18:50] we made it to the end of another exciting stat quest if you like this
[18:53] exciting stat quest if you like this stack quest and want to see more please
[18:55] stack quest and want to see more please subscribe and if you want to support
[18:57] subscribe and if you want to support stack quest consider buying one or two
[18:59] stack quest consider buying one or two of my original songs or a t-shirt or a
[19:01] of my original songs or a t-shirt or a hoodie or just donate the links are in
[19:04] hoodie or just donate the links are in the description below alright until next
[19:07] the description below alright until next time quest on

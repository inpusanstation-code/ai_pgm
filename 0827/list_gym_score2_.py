scores = [10.0, 9.0, 8.3, 7.1, 3.0, 9.0]
print("제거전", scores)
scores.sort() 

sorted = sorted(scores)
print("sorted ver: ", sorted)

new_scores = scores[1:-1] 
print("제거후", new_scores)

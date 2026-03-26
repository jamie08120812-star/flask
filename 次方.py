x = int(input("x:"))
opt = input("運算:∧(次方)√(根號)")
y = int(input("y:"))

if opt == "∧":
  result = x ** y
elif opt == "√":
  if result == 0:
    result ="數學不能問0次方"
  else:
    result = x ** (1/y)
else:
    result ="請輸入∧成√"
print(result)


from textblob import TextBlob

text="Hello"
blob=TextBlob(text)

print(blob.translate(to='ja'))
print(blob.translate(to='fr'))
print(blob.translate(to='de'))

text2="Hel you"
blob=TextBlob(text2)

print(blob.translate(to='ja'))
in cmd

For English:

type text_en.txt | piper.exe -m en_US-hfc_female-medium.onnx -f voice_en.wav



For Turkish:

chcp 65001	(1 kez çalıştırsan yeter bunu cmd kapanana kadar geçerli türkçe karakter desteği için)

type text_tr.txt | piper.exe -m tr_TR-dfki-medium.onnx -f voice_tr.wav

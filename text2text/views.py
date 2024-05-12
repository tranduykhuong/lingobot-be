import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from transformers import T5Tokenizer, T5ForConditionalGeneration
from nltk.translate.bleu_score import sentence_bleu

from api.utils import (try_except_wrapper)

from paraphrase_metrics import metrics as pm
import spacy
nlp = spacy.load("en_core_web_sm")

class Text2TextApi(ViewSet):
    @action(
        detail=False,
        methods=["POST"],
        url_path="score",
        url_name="score",
    )
    @try_except_wrapper
    def score(self, request):
        body = json.loads(request.body)
        
        input_text = body['input']
        output_text = body['output']
        
        reference = [input_text.split()]
        candidate = output_text.split()

        bleu_score = sentence_bleu(reference, candidate)

        s = nlp(input_text)
        t = nlp(output_text)

        wpd = pm.wpd(s,t)
        ld = pm.ld(s,t)
        
        return Response(
            data={
                "bleu_score": bleu_score,
                "wpd": wpd,
                "ld": ld
            },
            status=status.HTTP_200_OK,
        )

    # tokenizer = T5Tokenizer.from_pretrained("google-t5/t5-base")
    # model = T5ForConditionalGeneration.from_pretrained(
    #     pretrained_model_name_or_path='text2text/chatgpt_paraphraser_T5_base', 
    #     local_files_only=True,
    # )

    # @action(
    #     detail=False,
    #     methods=["POST"],
    #     url_path="summary",
    #     url_name="summary",
    # )
    # @try_except_wrapper
    # def summary(self, request):
    #     task_prefix = 'summarize: '
    #     sequence = request.data.get('sequence')
    
    #     inputs = self.tokenizer([task_prefix + sequence], return_tensors="pt", padding=True)
    #     generated_ids = self.model.generate(
    #                 input_ids = inputs['input_ids'],
    #                 attention_mask = inputs['attention_mask'], 
    #                 max_length=150, 
    #                 num_beams=2,
    #                 repetition_penalty=2.5, 
    #                 length_penalty=1.0, 
    #                 early_stopping=True
    #                 )
    #     preds = [self.tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=True) for g in generated_ids]

    #     return Response(
    #             data=preds[0],
    #             status=status.HTTP_200_OK,
    #         )
    
    # @action(
    #     detail=False,
    #     methods=["POST"],
    #     url_path="paraphrase",
    #     url_name="paraphrase",
    # )
    # @try_except_wrapper
    # def paraphrase(self, request):
    #     task_prefix = 'paraphrase: '
    #     # task_prefix = 'Generate Paraphrase for this line: '
    #     sequence = request.data.get('sequence')
    
    #     inputs = self.tokenizer([task_prefix + sequence], return_tensors="pt", padding=True)
    #     generated_ids = self.model.generate(
    #                 input_ids = inputs['input_ids'],
    #                 attention_mask = inputs['attention_mask'], 
    #                 max_length=150, 
    #                 num_beams=3,
    #                 repetition_penalty=2.5, 
    #                 length_penalty=1.0, 
    #                 early_stopping=True,
    #                 num_return_sequences=3
    #                 )
    #     preds = [self.tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=True) for g in generated_ids]

    #     return Response(
    #             data=preds,
    #             status=status.HTTP_200_OK,
    #         )
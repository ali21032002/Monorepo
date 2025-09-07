from typing import Any, Dict, List

from .schemas import get_schema_instructions


FEW_SHOT_FA: List[Dict[str, Any]] = [
	{
		"text": "علی در تهران زندگی می‌کند و در شرکت دیجی‌کالا کار می‌کند.",
		"entities": [
			{"name": "علی", "type": "PERSON"},
			{"name": "تهران", "type": "LOCATION"},
			{"name": "دیجی‌کالا", "type": "ORGANIZATION"},
		],
		"relationships": [
			{"source_entity_id": "PERSON:علی", "target_entity_id": "ORGANIZATION:دیجی‌کالا", "type": "EMPLOYED_AT"},
			{"source_entity_id": "PERSON:علی", "target_entity_id": "LOCATION:تهران", "type": "LIVES_IN"},
		],
	},
]

# Police domain example with inference
FEW_SHOT_POLICE_FA: List[Dict[str, Any]] = [
	{
		"text": "شخصی با نام احمد رضایی وارد مغازه شد، کالایی برداشت و بدون پرداخت خارج شد.",
		"entities": [
			{"name": "احمد رضایی", "type": "SUSPECT"},
			{"name": "مغازه", "type": "LOCATION"},
			{"name": "کالا برداشتن بدون پرداخت", "type": "SUSPICIOUS_BEHAVIOR"},
			{"name": "احتمال سرقت", "type": "CRIMINAL_INFERENCE"},
		],
		"relationships": [
			{"source_entity_id": "SUSPECT:احمد رضایی", "target_entity_id": "LOCATION:مغازه", "type": "ENTERED"},
			{"source_entity_id": "SUSPECT:احمد رضایی", "target_entity_id": "SUSPICIOUS_BEHAVIOR:کالا برداشتن بدون پرداخت", "type": "PERFORMED"},
			{"source_entity_id": "SUSPICIOUS_BEHAVIOR:کالا برداشتن بدون پرداخت", "target_entity_id": "CRIMINAL_INFERENCE:احتمال سرقت", "type": "INDICATES"},
		],
	},
]

FEW_SHOT_EN: List[Dict[str, Any]] = [
	{
		"text": "Sara moved to Berlin in 2019 and works at Google.",
		"entities": [
			{"name": "Sara", "type": "PERSON"},
			{"name": "Berlin", "type": "LOCATION"},
			{"name": "2019", "type": "DATE"},
			{"name": "Google", "type": "ORGANIZATION"},
		],
		"relationships": [
			{"source_entity_id": "PERSON:Sara", "target_entity_id": "LOCATION:Berlin", "type": "MOVED_TO"},
			{"source_entity_id": "PERSON:Sara", "target_entity_id": "ORGANIZATION:Google", "type": "EMPLOYED_AT"},
		],
	},
]

# Domain-specific prompts
DOMAIN_PROMPTS = {
	"general": {
		"fa": "شما یک موتور استخراج اطلاعات دقیق هستید. متن‌های عمومی را تحلیل کنید و موجودیت‌ها، روابط و استنتاج‌های منطقی را شناسایی کنید. احتمالات و ریسک‌ها را ارزیابی کنید.",
		"en": "You are a precise information extraction engine for general texts. Identify important entities, relationships, and logical inferences. Assess probabilities and risks."
	},
	"legal": {
		"fa": "شما یک متخصص حقوقی هستید که متن‌های قانونی را تحلیل می‌کنید. بر اشخاص، نهادهای حقوقی، قوانین، مواد قانونی، دادگاه‌ها، قراردادها و روابط حقوقی تمرکز کنید. احتمال نقض قوانین و خطرات حقوقی را ارزیابی کنید.",
		"en": "You are a legal expert analyzing legal texts. Focus on persons, legal entities, laws, legal articles, courts, contracts, and legal relationships. Assess probability of law violations and legal risks."
	},
	"medical": {
		"fa": "شما یک متخصص پزشکی هستید که اسناد پزشکی را تحلیل می‌کنید. بر بیماران، پزشکان، بیماری‌ها، علائم، درمان‌ها، داروها، آزمایش‌ها و روابط پزشکی تمرکز کنید. خطرات سلامتی و احتمالات تشخیصی را ارزیابی کنید.",
		"en": "You are a medical expert analyzing medical documents. Focus on patients, doctors, diseases, symptoms, treatments, medications, tests, and medical relationships. Assess health risks and diagnostic probabilities."
	},
	"police": {
		"fa": "شما یک تحلیلگر امنیتی هستید که اسناد پلیسی و امنیتی را بررسی می‌کنید. بر مظنونان، مجرمان، جرائم، شاهدان، مکان‌های وقوع، زمان، شواهد و روابط جرمی تمرکز کنید. رفتارهای مشکوک، انگیزه‌های احتمالی، و سطح تهدید را تحلیل و استنتاج کنید. احتمال وقوع جرم را ارزیابی کنید.",
		"en": "You are a security analyst reviewing police and security documents. Focus on suspects, criminals, crimes, witnesses, locations, times, evidence, and criminal relationships. Analyze and infer suspicious behaviors, potential motives, and threat levels. Assess crime probability."
	}
}

# Domain-specific entity types
DOMAIN_ENTITY_TYPES = {
	"general": ["PERSON", "ORGANIZATION", "LOCATION", "DATE", "TIME", "EVENT", "PRODUCT", "MONEY", "INFERENCE", "RISK_ASSESSMENT"],
	"legal": ["PERSON", "LEGAL_ENTITY", "COURT", "LAW", "LEGAL_ARTICLE", "CONTRACT", "CASE_NUMBER", "DATE", "LOCATION", "FINE", "SENTENCE", "LEGAL_INFERENCE", "VIOLATION_RISK"],
	"medical": ["PATIENT", "DOCTOR", "HOSPITAL", "DISEASE", "SYMPTOM", "TREATMENT", "MEDICATION", "TEST", "BODY_PART", "DATE", "DOSAGE", "MEDICAL_INFERENCE", "HEALTH_RISK"],
	"police": ["SUSPECT", "VICTIM", "WITNESS", "CRIME", "LOCATION", "DATE", "TIME", "EVIDENCE", "WEAPON", "VEHICLE", "CASE_NUMBER", "OFFICER", "CRIMINAL_INFERENCE", "THREAT_LEVEL", "MOTIVE", "SUSPICIOUS_BEHAVIOR"]
}


def build_system_prompt(*, language: str, schema_name: str, domain: str = "general") -> str:
	schema_instruction = get_schema_instructions(schema_name)
	
	# Get domain-specific prompt
	domain_prompt = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS["general"])
	domain_instruction = domain_prompt.get(language, domain_prompt["en"])
	
	# Get domain-specific entity types
	entity_types = DOMAIN_ENTITY_TYPES.get(domain, DOMAIN_ENTITY_TYPES["general"])
	entity_types_str = ", ".join(entity_types)
	
	return (
		f"{domain_instruction}\n"
		f"Focus on these entity types: {entity_types_str}\n"
		"Output only minified JSON that conforms to the schema. "
		"Do not include any explanations or extra text.\n\n" + schema_instruction
	)


def build_user_prompt(*, text: str, language: str, examples: List[Dict[str, Any]], domain: str = "general") -> str:
	few_shots = examples
	if not few_shots:
		# Use domain-specific examples if available
		if domain == "police" and language.lower().startswith("fa"):
			few_shots = FEW_SHOT_POLICE_FA
		else:
			few_shots = FEW_SHOT_FA if language.lower().startswith("fa") else FEW_SHOT_EN

	shots_str_items: List[str] = []
	for ex in few_shots:
		shots_str_items.append(
			f"TEXT:\n{ex['text']}\nJSON:\n" + "{" + f"\"entities\": {ex.get('entities', [])}, \"relationships\": {ex.get('relationships', [])}" + "}"
		)
	shots_str = "\n\n".join(shots_str_items)

	# Domain-specific inference instructions
	inference_instructions = {
		"general": {
			"fa": "علاوه بر موجودیت‌ها و روابط مستقیم، استنتاج‌های منطقی و احتمالات را نیز شناسایی کنید.",
			"en": "In addition to direct entities and relationships, identify logical inferences and probabilities."
		},
		"police": {
			"fa": "ویژه: رفتارهای مشکوک، احتمال وقوع جرم، انگیزه‌های احتمالی و سطح تهدید را تحلیل و استنتاج کنید. اگر متن حاکی از احتمال جرم است، آن را به عنوان CRIMINAL_INFERENCE یا SUSPICIOUS_BEHAVIOR شناسایی کنید.",
			"en": "Special: Analyze and infer suspicious behaviors, crime probability, potential motives, and threat levels. If the text suggests possible crime, identify it as CRIMINAL_INFERENCE or SUSPICIOUS_BEHAVIOR."
		},
		"legal": {
			"fa": "ویژه: احتمال نقض قوانین، خطرات حقوقی و استنتاج‌های قانونی را شناسایی کنید.",
			"en": "Special: Identify probability of law violations, legal risks, and legal inferences."
		},
		"medical": {
			"fa": "ویژه: خطرات سلامتی، احتمالات تشخیصی و استنتاج‌های پزشکی را شناسایی کنید.",
			"en": "Special: Identify health risks, diagnostic probabilities, and medical inferences."
		}
	}
	
	domain_instruction = inference_instructions.get(domain, inference_instructions["general"])
	instruction_text = domain_instruction.get(language, domain_instruction["en"])

	return (
		f"LANGUAGE: {language}\n"
		"Return JSON with keys: entities, relationships. Entities need name and type.\n"
		f"{instruction_text}\n"
		"If unsure, leave arrays empty.\n\n"
		f"FEW-SHOTS:\n{shots_str}\n\n"
		f"NOW EXTRACT FROM THIS TEXT:\n{text}\n"
	)


def build_referee_prompt(*, text: str, language: str, first_analysis: Dict[str, Any], second_analysis: Dict[str, Any], domain: str = "general") -> str:
	"""Build prompt for referee model to make final decision"""
	
	domain_context = {
		"general": {"fa": "تحلیل عمومی متن", "en": "general text analysis"},
		"legal": {"fa": "تحلیل متن حقوقی", "en": "legal text analysis"}, 
		"medical": {"fa": "تحلیل متن پزشکی", "en": "medical text analysis"},
		"police": {"fa": "تحلیل متن امنیتی/پلیسی", "en": "police/security text analysis"}
	}
	
	context = domain_context.get(domain, domain_context["general"])
	context_str = context.get(language, context["en"])
	
	if language.lower().startswith("fa"):
		inference_note = ""
		if domain == "police":
			inference_note = "\nتوجه ویژه: رفتارهای مشکوک، احتمالات جرمی، انگیزه‌ها و استنتاج‌های امنیتی را در نظر بگیرید."
		elif domain == "legal":
			inference_note = "\nتوجه ویژه: احتمال نقض قوانین و خطرات حقوقی را ارزیابی کنید."
		elif domain == "medical":
			inference_note = "\nتوجه ویژه: خطرات سلامتی و احتمالات تشخیصی را در نظر بگیرید."
		
		prompt = f"""شما یک داور متخصص برای {context_str} هستید. دو تحلیل زیر را بررسی کنید و بهترین تحلیل نهایی را ارائه دهید.{inference_note}

متن اصلی:
{text}

تحلیل مدل اول:
موجودیت‌ها: {first_analysis.get('entities', [])}
روابط: {first_analysis.get('relationships', [])}

تحلیل مدل دوم:  
موجودیت‌ها: {second_analysis.get('entities', [])}
روابط: {second_analysis.get('relationships', [])}

لطفاً:
1. موجودیت‌ها و روابط هر دو تحلیل را بررسی کنید
2. موارد مشترک و متفاوت را شناسایی کنید
3. بهترین ترکیب را انتخاب کنید یا تحلیل بهتری ارائه دهید
4. استنتاج‌های منطقی و احتمالات را در نظر بگیرید
5. فقط JSON خروجی بدهید، بدون توضیح اضافی

خروجی نهایی:"""
	else:
		prompt = f"""You are an expert referee for {context_str}. Review the two analyses below and provide the best final analysis.

Original text:
{text}

First model analysis:
Entities: {first_analysis.get('entities', [])}
Relationships: {first_analysis.get('relationships', [])}

Second model analysis:
Entities: {second_analysis.get('entities', [])}  
Relationships: {second_analysis.get('relationships', [])}

Please:
1. Review entities and relationships from both analyses
2. Identify common and different items
3. Select the best combination or provide better analysis
4. Output only JSON, no additional explanations

Final output:"""
	
	return prompt

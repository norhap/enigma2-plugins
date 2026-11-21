def search_results(data):
	results = []
	for item in data.get("results", []):
		kind = item.get("media_type")
		ident = item.get("id")
		name = item.get("title") if kind == "movie" else item.get("name")
		if kind not in ("movie", "tv") or not isinstance(ident, int) or not name:
			continue
		date = item.get("release_date") if kind == "movie" else item.get("first_air_date")
		label = "%s (%s)" % (name, date[:4]) if date else name
		results.append((label, "tmdb:%s:%d" % (kind, ident), item.get("overview") or ""))
	return results


def title_data(data, kind, ident):
	name = data.get("title") if kind == "movie" else data.get("name")
	if not name or data.get("id") != ident:
		raise ValueError("TMDB title response does not match the requested title")
	original = data.get("original_title") if kind == "movie" else data.get("original_name")
	date = data.get("release_date") if kind == "movie" else data.get("first_air_date")
	cast = []
	for person in (data.get("credits") or {}).get("cast", [])[:18]:
		if person.get("name"):
			characters = [{"node": {"name": person["character"]}}] if person.get("character") else []
			cast.append({"name": {"nameText": {"text": person["name"]}},
				"creditedRoles": {"edges": [{"node": {"characters": {"edges": characters}}}]}})
	crew = []
	for job, group in (("Director", "amzn1.imdb.concept.name_credit_category.ace5cb4c-8708-4238-9542-04641e7c8171"),
			("Writer", "amzn1.imdb.concept.name_credit_category.c84ecaff-add5-4f2e-81db-102a41881fe3")):
		names = [p.get("name") for p in (data.get("credits") or {}).get("crew", [])
			if p.get("job") == job and p.get("name")]
		if names:
			crew.append({"grouping": {"groupingId": group},
				"credits": [{"name": {"nameText": {"text": n}}} for n in names]})
	release = {}
	if date:
		parts = date.split("-")
		if len(parts) == 3 and all(part.isdigit() for part in parts):
			release = {"year": int(parts[0]), "month": int(parts[1]), "day": int(parts[2]),
				"displayableProperty": {"value": {"plainText": date}}}
	runtime = data.get("runtime") or next(iter(data.get("episode_run_time") or []), None)
	title = {
		"id": "tmdb:%s:%d" % (kind, ident),
		"titleText": {"text": name},
		"originalTitleText": {"text": original or name},
		"genres": {"genres": [{"text": x["name"]} for x in data.get("genres", []) if x.get("name")]},
		"crewV2": crew,
		"castV2": {"credits": cast},
		"releaseDate": release,
		"episodes": {"episodes": {"total": data.get("number_of_episodes")},
			"displayableSeasons": {"total": data.get("number_of_seasons")}},
		"plot": {"plotText": {"plainText": data.get("overview") or ""}},
		"taglines": {"edges": [{"node": {"text": data.get("tagline")}}]} if data.get("tagline") else {},
		"countriesOfOrigin": {"countries": [{"text": x["name"]} for x in data.get("production_countries", []) if x.get("name")]},
		"spokenLanguages": {"spokenLanguages": [{"text": x["name"]} for x in data.get("spoken_languages", []) if x.get("name")]},
	}
	if data.get("vote_count") and isinstance(data.get("vote_average"), (int, float)):
		title["ratingsSummary"] = {"aggregateRating": data["vote_average"]}
	if runtime:
		title["runtime"] = {"displayableProperty": {"value": {"plainText": "%s min" % runtime}}}
	if data.get("poster_path"):
		title["primaryImage"] = {"url": "https://image.tmdb.org/t/p/w500" + data["poster_path"]}
	return title

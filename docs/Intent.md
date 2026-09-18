# Project Name

OCRAgent

## Problem Statement

Documents provide a "human-level" way to transfer information but encoding data via characters printed on paper is difficult for machines to understand. The first level of the problem is extracting individual characters. The rest of the problem is extracting meaning from the characters, and that meaning is derived from the physical position of the characters.  Characters that are physically next to each other become words and collections of words build paragraphs or blocks of data. The overall structure of the document and the location of the lines, paragraphs or blocks on the page also provide meaning: a "letter" has a specific format and, within the context of that format, a group of lines near a corner of the page are often an address block that appears in a window in an envelope while a few lines of text below a signature or closing statement can tell the reader who sent the document. 

From this overview, we can see that, in order to support data transfer using documents as the transfer medium, we need to solve three problems:

1. Extract the individual characters

2. Combine them into meaningful groups or clusters of data

3. Infer the structure of the document

Of these, this application's ability to infer the structure of the document is limited; a few document types such as a "letter", a "claim" (meaning an invoice or bill) or a statement have readily identifiable structures but many other document types exist that are difficult to recognize. For this solution, the ability to recognize the document type will not be provided. However, an application or system that has additional context about the document (e.g. the document was produced by a claims process that only produces three types of documents) may be able to infer the document type from information about the clustering of the data. This application can provide that clustering information because it is derived from the individual characters.

The ability to recognize characters is affected by the fidelity of the document and the typography used. If the text can be extracted directly from the digital format of the document (e.g. the text layer of a PDF) this application can have higher confidence that the text is valid than if it is trying to recognize the shapes of the characters from a JPEG image. This "recognition confidence" is important. If an application is scanning a bank statement to extract data about a single transaction, and if it has access to bank account data from another source, then, if it can extract the account number and the statement starting date it may have all it needs, so 100% confidence on two fields would be sufficient for that purpose. At the other extreme, if the application is trying to read a medical history, it may require 95% confidence on all fields for the entire history to determine if it has what is needed. Also, if the consuming application is only concerned about the structure of the document (that is, it is trying to understand the structure of a "letter document"), it may not be concerned about the data values from the document.

This application does not have the broader context to know in which of these scenarios it is operating. Also, if the consuming application is agentic, that application may be able to adapt its processing of the results based on the confidence levels reported. To support this, this application must provide a count of the number of fields whose extraction confidence exceeds a provided minimum level, the confidence score for the recognized value for each data field and an overall confidence score.

The overall confidence score is the numeric sum of all individual field confidence scores. By itself, the overall confidence score provides a "low-bar" result. To illustrate the problem, let's assume the consuming application is expecting 10 fields and it can accept the result if there is an 85% confidence level for each which means it can accept the result if the overall confidence score is greater than 8.5. Let's assume this application scans the document, has 100% confidence on nine fields and it misses one field entirely. As a result, the application will return a 90% confidence which exceeds the stated minimum, but the scan has not met the intended threshold. This is why this application must also return the number of fields extracted. Combined, these numbers provide a more useful result. In the example above, by returning a count of nine extracted field values the consuming application can immediately determine that the threshold has not been met. 

A further improvement can be made if the consuming application provides a minimum acceptable extraction confidence level for a field; if the consuming application provides a minimum extraction confidence requirement of 50% for each field and this application has a 30% confidence for one field, that field would not be counted in the number of fields recognized (the field results are still included in the field list, but not included in the count).

Other statistics were considered, such as the average confidence level. This application is stopping one mathematical step short of that by returning the raw total and the number of accepted fields. Other than bounding the range of the result across documents with varying field counts, the average is not providing new information that is significantly better than the component values. If the consuming application does not know how many fields it expects it can easily compute the average from the data returned. Likewise, if the consuming application needs more detailed statistics such as the mean and standard deviation, it can compute those values from the scores returned for each field.

## Core Capabilities

This application provides a capability that must be hosted by a consuming application. It accepts a PDF and extracts structure, data and extraction confidence information from it. It is assumed that the PDF contains a single page; it is up to the consuming application to "burst" multipage documents into individual pages. This side-steps issues such as how would the consuming application pass a 600 page PDF to this application.

A "per field" minimum extraction confidence threshold and an overall acceptable extraction score (which is the minimum allowed value for the sum of all field confidence values) must be provided by the consuming application. This application will use these values to determine the number of fields with acceptable extraction confidence and a "pass/fail" flag indicating whether the overall score was met. It is known that some PDFs are produced from other print formats such as AFP. For AFP specifically, it is known that the PDF does not contain a clear text layer; instead, it contains raster scan images that must be scanned visually. To help the consuming application evaluate the results, an indicator of the extraction method will be returned (e.g. "visual" if extracted from imagery, "digital" if extracted from a text layer in the file)

This application always returns whatever it can obtain for each field that it can identify. All other returned values are derived from this component data.

The term "structure" means the location of each recognized data item and the relationship of this item to the other data items near it will be used to recognize tables, paragraphs and lists. Data within recognized tables will be returned in two-dimensional arrays organized by row, content recognized in bullet lists and numbered lists will be collected into one-dimensional arrays, consecutive lines of text will be collected into one-dimensional arrays (one item for each line) as "paragraphs". 

Constraints: blocks of lines will be presented as a "paragraph" regardless of the overall context as it's not possible for this application to be certain of the context of the text block; a group of lines of text at the top of a document might be an address or they might be reference data but this application does not have the context to make that call.

## Primary users

This application will be a capability that can be integrated into other applications. It is not known how the consuming application will use it: the consuming application may be extracting document structure to build document format specifications, it may be extracting key values that will be used to obtain other information perhaps to support a customer service activity or it may be summarizing a document and presenting the extracted data along with the summary in a form.

## Performance

There is no specific performance specification for this application. Some earlier testing suggests that it may take up to one minute to process some single page documents based on the format of the document (e.g. AFP converted to PDF) and the hardware that runs the application.

## Security

Because this product provides a capability on which other services are built, it assumes the issues of authentication and authorization will be handled by the consuming application or service. However, this product must not leak extracted information outside this scope. For an example of this risk (and an example of what to look for in the chosen technology), a prototype of this product was built using PaddleOCR and a model hosted by Ollama; both of these capabilities have the ability to connect to the Internet and might pass data to their hosting service.

This application does not retain any of the provided information. 

Because this capability is hosted by a consuming application, it is not known how the PDF data will be provided to it or what the context of the data is. As a result, issues around Personally Identifying Information (PII) must be handled by the consuming application.

## Other Non-functional Requirements (NFRs)

No other specifications for non-functional requirements are known at this time. It is assumed the process may add additional NFRs.

## Out of Scope

A version 2 feature will be to allow a record structure to be provided and the data from this tool will be returned in that form. 

## Success Criteria

This tool must know what it does not know. It meets the requirement by applying a "minimum confidence threshold" (provided by the consuming application) to determine if a field can be included in the extraction count, returning a confidence score for every extracted data item, the number of fields with extraction confidence above the minimum level and the method used to extract the data (e.g. visual versus digital extraction). Data will be grouped by related structure for the single page passed in. 

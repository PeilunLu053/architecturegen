def test_vectorizer_detects_components(tmp_path):
    image = [[0 for _ in range(10)] for _ in range(10)]
    for y in range(1, 4):
        for x in range(1, 4):
            image[y][x] = 1
    for y in range(6, 9):
        for x in range(6, 9):
            image[y][x] = 1

    from img2cad.converter import ImageToCadConverter

    converter = ImageToCadConverter()
    output = tmp_path / "out.dxf"
    converter.convert_from_array(image, output)

    content = output.read_text().splitlines()
    # Ensure two polylines were written (two occurrences of LWPOLYLINE entity)
    assert content.count("LWPOLYLINE") == 2


def test_processing_threshold(tmp_path):
    raw = [[[255, 255, 255] for _ in range(5)] for _ in range(5)]
    raw[0][0] = [0, 0, 0]

    from img2cad.converter import ConversionConfig, ImageToCadConverter
    from img2cad.image_processing import ProcessingConfig
    from img2cad.vectorization import VectorizerConfig

    converter = ImageToCadConverter(
        config=ConversionConfig(
            processing=ProcessingConfig(threshold=200),
            vectorizer=VectorizerConfig(min_component_size=1),
        )
    )
    output = tmp_path / "threshold.dxf"
    converter.convert_from_array(raw, output)

    content = output.read_text()
    # With a high threshold only the white area should be ignored; we expect
    # a single bounding box to be written.
    assert content.count("LWPOLYLINE") == 1

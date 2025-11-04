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


def test_vectorizer_traces_outline():
    image = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]

    from img2cad.vectorization import Vectorizer, VectorizerConfig

    vectorizer = Vectorizer()
    shapes = vectorizer.vectorize(image, VectorizerConfig(min_component_size=1))
    assert len(shapes) == 1
    polygon = shapes[0].points
    # Expect an outline with more than the four points of a simple bounding box
    assert len(polygon) > 4
    # Ensure the outline starts at the lower-most x/y coordinate
    xs = [x for x, _ in polygon]
    ys = [y for _, y in polygon]
    assert min(xs) == 1.0
    assert min(ys) == 1.0


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
    # a single outline to be written.
    assert content.count("LWPOLYLINE") == 1


def test_simplification_respects_tolerance():
    image = [
        [0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 1, 0],
        [0, 1, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0],
    ]

    from img2cad.vectorization import Vectorizer, VectorizerConfig

    vectorizer = Vectorizer()
    unsimplified = vectorizer.vectorize(
        image,
        VectorizerConfig(min_component_size=1, simplify=False),
    )[0].points
    simplified = vectorizer.vectorize(
        image,
        VectorizerConfig(min_component_size=1, simplify=True, simplify_tolerance=0.5),
    )[0].points

    assert len(simplified) < len(unsimplified)
    assert simplified[0] == unsimplified[0]
